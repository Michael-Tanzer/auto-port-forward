import logging
import signal
import threading
import webbrowser

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from config import load_config, get_ssh_connections, get_tunnels, get_web_port
from tunnels import TunnelManager
from web import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def create_icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Dark rounded background
    draw.rounded_rectangle([2, 2, 62, 62], radius=12, fill="#1a1a1a")
    # Two vertical bars (tunnel ends)
    draw.rectangle([14, 16, 22, 48], fill="#4caf50")
    draw.rectangle([42, 16, 50, 48], fill="#4caf50")
    # Arrow in the middle
    draw.polygon([(26, 26), (38, 32), (26, 38)], fill="#4caf50")
    return img


def auto_start_tunnels(manager: TunnelManager):
    doc = load_config()
    ssh_conns = get_ssh_connections(doc)
    for t in get_tunnels(doc):
        if not t.get("enabled", False):
            continue
        ssh_name = t.get("ssh")
        ssh_cfg = ssh_conns.get(ssh_name)
        if not ssh_cfg:
            log.warning("Tunnel '%s' references unknown SSH connection '%s'", t["name"], ssh_name)
            continue
        status = manager.start_tunnel(t["name"], ssh_cfg, t)
        log.info("Auto-start '%s': %s", t["name"], status)


def main():
    manager = TunnelManager()
    doc = load_config()
    web_port = get_web_port(doc)

    app = create_app(manager)

    flask_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=web_port, use_reloader=False),
        daemon=True,
    )
    flask_thread.start()

    auto_start_tunnels(manager)

    url = f"http://127.0.0.1:{web_port}"

    def open_ui(icon, item):
        webbrowser.open(url)

    def quit_app(icon, item):
        manager.stop_all()
        icon.stop()

    icon = Icon(
        "auto-port-forward",
        icon=create_icon_image(),
        title="Auto Port Forward",
        menu=Menu(
            MenuItem("Open UI", open_ui, default=True),
            MenuItem("Quit", quit_app),
        ),
    )
    def shutdown(signum, frame):
        log.info("Caught signal %s, shutting down…", signum)
        manager.stop_all()
        icon.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log.info("Tray icon running. UI at %s", url)
    icon.run()


if __name__ == "__main__":
    main()
