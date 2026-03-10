import os
import logging
import select
import socketserver
import threading

import paramiko

log = logging.getLogger(__name__)


class _ForwardHandler(socketserver.BaseRequestHandler):
    """Handles one incoming local connection by forwarding it through SSH."""

    # Set by SSHTunnel before constructing the server
    ssh_transport: paramiko.Transport
    remote_host: str
    remote_port: int

    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                "direct-tcpip",
                (self.remote_host, self.remote_port),
                self.request.getpeername(),
            )
        except Exception as e:
            log.debug("Channel open failed: %s", e)
            return
        if chan is None:
            return

        try:
            while True:
                r, _, _ = select.select([self.request, chan], [], [], 1.0)
                if self.request in r:
                    data = self.request.recv(4096)
                    if not data:
                        break
                    chan.sendall(data)
                if chan in r:
                    data = chan.recv(4096)
                    if not data:
                        break
                    self.request.sendall(data)
        except Exception:
            pass
        finally:
            chan.close()
            self.request.close()


class _ForwardServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class SSHTunnel:
    """A single SSH tunnel: listens locally and forwards through an SSH connection."""

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_username: str,
        remote_host: str,
        remote_port: int,
        local_port: int,
        ssh_key_file: str | None = None,
        ssh_password: str | None = None,
    ):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_port = local_port
        self.ssh_key_file = ssh_key_file
        self.ssh_password = ssh_password

        self._client: paramiko.SSHClient | None = None
        self._server: _ForwardServer | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(
            hostname=self.ssh_host,
            port=self.ssh_port,
            username=self.ssh_username,
            key_filename=self.ssh_key_file,
            password=self.ssh_password,
        )
        transport = self._client.get_transport()
        transport.set_keepalive(30)

        # Build a handler subclass bound to this tunnel's SSH transport
        class Handler(_ForwardHandler):
            ssh_transport = transport
            remote_host = self.remote_host
            remote_port = self.remote_port

        self._server = _ForwardServer(("127.0.0.1", self.local_port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._client:
            self._client.close()
            self._client = None
        self._thread = None

    @property
    def is_active(self) -> bool:
        if self._client is None:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()


class TunnelManager:
    def __init__(self):
        self._tunnels: dict[str, SSHTunnel] = {}
        self._errors: dict[str, str] = {}
        self._desired_running: dict[str, tuple[dict, dict]] = {}
        self._lock = threading.Lock()
        self._monitor_stop: threading.Event | None = None
        self._monitor_thread: threading.Thread | None = None

    def start_tunnel(self, name: str, ssh_config: dict, tunnel_config: dict) -> str:
        with self._lock:
            if name in self._tunnels:
                self._stop_unlocked(name)

            key_file = ssh_config.get("key_file", "")
            if key_file:
                key_file = os.path.expanduser(key_file)

            try:
                tunnel = SSHTunnel(
                    ssh_host=ssh_config["host"],
                    ssh_port=ssh_config.get("port", 22),
                    ssh_username=ssh_config.get("username"),
                    remote_host=tunnel_config.get("remote_host", "localhost"),
                    remote_port=tunnel_config["remote_port"],
                    local_port=tunnel_config["local_port"],
                    ssh_key_file=key_file or None,
                    ssh_password=ssh_config.get("password") or None,
                )
                tunnel.start()
                self._tunnels[name] = tunnel
                self._errors.pop(name, None)
                self._desired_running[name] = (ssh_config, tunnel_config)
                log.info(
                    "Tunnel '%s' started: localhost:%d -> %s:%d",
                    name,
                    tunnel_config["local_port"],
                    tunnel_config.get("remote_host", "localhost"),
                    tunnel_config["remote_port"],
                )
                return "connected"
            except Exception as e:
                self._errors[name] = str(e)
                log.error("Tunnel '%s' failed: %s", name, e)
                return f"error: {e}"

    def stop_tunnel(self, name: str) -> None:
        with self._lock:
            self._desired_running.pop(name, None)
            self._stop_unlocked(name)

    def _stop_unlocked(self, name: str) -> None:
        tunnel = self._tunnels.pop(name, None)
        self._errors.pop(name, None)
        if tunnel:
            try:
                tunnel.stop()
            except Exception:
                pass
            log.info("Tunnel '%s' stopped", name)

    def stop_all(self) -> None:
        with self._lock:
            self._desired_running.clear()
            for name in list(self._tunnels):
                self._stop_unlocked(name)

    def get_status(self, name: str) -> str:
        with self._lock:
            if name in self._errors:
                return f"error: {self._errors[name]}"
            tunnel = self._tunnels.get(name)
            if not tunnel:
                return "disconnected"
            try:
                if tunnel.is_active:
                    return "connected"
            except Exception:
                pass
            return "disconnected"

    def start_monitor(self, check_interval: int = 30):
        self._monitor_stop = threading.Event()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True,
        )
        self._monitor_thread.start()
        log.info("Tunnel health monitor started (interval=%ds)", check_interval)

    def stop_monitor(self):
        if self._monitor_stop:
            self._monitor_stop.set()

    def _monitor_loop(self, check_interval: int):
        backoff_base = 5
        backoff_max = 300
        retry_counts: dict[str, int] = {}

        while not self._monitor_stop.wait(check_interval):
            with self._lock:
                desired = dict(self._desired_running)

            for name, (ssh_config, tunnel_config) in desired.items():
                if self._monitor_stop.is_set():
                    return

                with self._lock:
                    tunnel = self._tunnels.get(name)
                    try:
                        is_healthy = tunnel is not None and tunnel.is_active
                    except Exception:
                        is_healthy = False

                if is_healthy:
                    retry_counts.pop(name, None)
                    continue

                failures = retry_counts.get(name, 0)
                backoff = min(backoff_base * (2 ** failures), backoff_max)
                log.info(
                    "Tunnel '%s' is down, attempting reconnect (attempt %d, backoff %ds)",
                    name, failures + 1, backoff,
                )

                # Clean up dead tunnel
                with self._lock:
                    old = self._tunnels.pop(name, None)
                if old:
                    try:
                        old.stop()
                    except Exception:
                        pass

                # Attempt reconnect
                try:
                    with self._lock:
                        if name not in self._desired_running:
                            continue

                    key_file = ssh_config.get("key_file", "")
                    if key_file:
                        key_file = os.path.expanduser(key_file)

                    new_tunnel = SSHTunnel(
                        ssh_host=ssh_config["host"],
                        ssh_port=ssh_config.get("port", 22),
                        ssh_username=ssh_config.get("username"),
                        remote_host=tunnel_config.get("remote_host", "localhost"),
                        remote_port=tunnel_config["remote_port"],
                        local_port=tunnel_config["local_port"],
                        ssh_key_file=key_file or None,
                        ssh_password=ssh_config.get("password") or None,
                    )
                    new_tunnel.start()

                    with self._lock:
                        self._tunnels[name] = new_tunnel
                        self._errors.pop(name, None)

                    retry_counts.pop(name, None)
                    log.info("Tunnel '%s' reconnected successfully", name)

                except Exception as e:
                    retry_counts[name] = failures + 1
                    with self._lock:
                        self._errors[name] = str(e)
                    log.warning(
                        "Tunnel '%s' reconnect failed: %s (next retry in ~%ds)",
                        name, e, backoff,
                    )
                    if self._monitor_stop.wait(backoff):
                        return
