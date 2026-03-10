import tomlkit
from flask import Flask, jsonify, request

from config import load_config, save_config, get_ssh_connections, get_tunnels
from tunnels import TunnelManager
from ui import HTML_PAGE


def create_app(tunnel_manager: TunnelManager) -> Flask:
    app = Flask(__name__)

    @app.errorhandler(Exception)
    def handle_error(e):
        return jsonify({"error": str(e)}), 500

    @app.route("/")
    def index():
        return HTML_PAGE

    # --- SSH connections ---

    @app.route("/api/ssh")
    def list_ssh():
        return jsonify(get_ssh_connections(load_config()))

    @app.route("/api/ssh/<name>", methods=["PUT"])
    def upsert_ssh(name):
        doc = load_config()
        if "ssh" not in doc:
            doc.add("ssh", tomlkit.table())
        t = tomlkit.table()
        for k, v in request.json.items():
            t.add(k, v)
        doc["ssh"][name] = t
        save_config(doc)
        return jsonify({"ok": True})

    @app.route("/api/ssh/<name>", methods=["DELETE"])
    def delete_ssh(name):
        doc = load_config()
        if "ssh" in doc and name in doc["ssh"]:
            del doc["ssh"][name]
            save_config(doc)
        return jsonify({"ok": True})

    # --- Tunnels ---

    @app.route("/api/tunnels")
    def list_tunnels():
        doc = load_config()
        tunnels = get_tunnels(doc)
        for t in tunnels:
            t["status"] = tunnel_manager.get_status(t["name"])
        return jsonify(tunnels)

    @app.route("/api/tunnels", methods=["POST"])
    def add_tunnel():
        doc = load_config()
        if "tunnels" not in doc:
            doc.add("tunnels", tomlkit.aot())
        new = tomlkit.table()
        data = request.json
        data.setdefault("enabled", True)
        for k, v in data.items():
            new.add(k, v)
        doc["tunnels"].append(new)
        save_config(doc)
        return jsonify({"ok": True})

    @app.route("/api/tunnels/<name>", methods=["PUT"])
    def update_tunnel(name):
        doc = load_config()
        tunnels = doc.get("tunnels", [])
        for t in tunnels:
            if t.get("name") == name:
                for k, v in request.json.items():
                    t[k] = v
                break
        save_config(doc)
        # Restart if running
        was_running = tunnel_manager.get_status(name) == "connected"
        if was_running:
            tunnel_manager.stop_tunnel(name)
            ssh_conns = get_ssh_connections(doc)
            tunnel_cfg = next((dict(t) for t in get_tunnels(doc) if t["name"] == name), None)
            if tunnel_cfg:
                ssh_cfg = ssh_conns.get(tunnel_cfg["ssh"])
                if ssh_cfg:
                    tunnel_manager.start_tunnel(name, ssh_cfg, tunnel_cfg)
        return jsonify({"ok": True})

    @app.route("/api/tunnels/<name>", methods=["DELETE"])
    def delete_tunnel(name):
        doc = load_config()
        tunnels = doc.get("tunnels", [])
        new_aot = tomlkit.aot()
        for t in tunnels:
            if t.get("name") != name:
                new_aot.append(t)
        doc["tunnels"] = new_aot
        save_config(doc)
        tunnel_manager.stop_tunnel(name)
        return jsonify({"ok": True})

    # --- Tunnel actions ---

    @app.route("/api/tunnels/<name>/start", methods=["POST"])
    def start_tunnel(name):
        doc = load_config()
        ssh_conns = get_ssh_connections(doc)
        tunnel_cfg = next((t for t in get_tunnels(doc) if t["name"] == name), None)
        if not tunnel_cfg:
            return jsonify({"error": "Tunnel not found"}), 404
        ssh_cfg = ssh_conns.get(tunnel_cfg.get("ssh"))
        if not ssh_cfg:
            return jsonify({"error": f"SSH connection '{tunnel_cfg.get('ssh')}' not found"}), 404
        status = tunnel_manager.start_tunnel(name, ssh_cfg, tunnel_cfg)
        return jsonify({"status": status})

    @app.route("/api/tunnels/<name>/stop", methods=["POST"])
    def stop_tunnel(name):
        tunnel_manager.stop_tunnel(name)
        return jsonify({"status": "disconnected"})

    return app
