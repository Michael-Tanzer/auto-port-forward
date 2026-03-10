import tomlkit
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.toml"

DEFAULT_CONFIG = """\
[settings]
web_port = 9876

# SSH connections — add one section per host:
# [ssh.myserver]
# host = "myserver.example.com"
# port = 22
# username = "user"
# key_file = "~/.ssh/id_rsa"
# password = ""

# Tunnels — add one [[tunnels]] block per forward:
# [[tunnels]]
# name = "Database"
# ssh = "myserver"
# remote_host = "localhost"
# remote_port = 5432
# local_port = 5432
# enabled = true
"""


def load_config() -> tomlkit.TOMLDocument:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return tomlkit.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(doc: tomlkit.TOMLDocument) -> None:
    CONFIG_PATH.write_text(tomlkit.dumps(doc), encoding="utf-8")


def get_ssh_connections(doc: tomlkit.TOMLDocument) -> dict:
    return {k: dict(v) for k, v in doc.get("ssh", {}).items()}


def get_tunnels(doc: tomlkit.TOMLDocument) -> list[dict]:
    return [dict(t) for t in doc.get("tunnels", [])]


def get_web_port(doc: tomlkit.TOMLDocument) -> int:
    return doc.get("settings", {}).get("web_port", 9876)
