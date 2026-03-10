import os
import logging
import select
import socket
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
        self._lock = threading.Lock()

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
