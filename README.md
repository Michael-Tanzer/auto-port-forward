# Auto Port Forward

Manage SSH port-forwarding tunnels through a web UI and system tray icon. Define SSH connections and tunnels in a simple TOML config, then start/stop them with a click.

## Features

- **Web UI** — add, edit, delete SSH connections and tunnels from the browser
- **System tray icon** — quick access to the UI and graceful quit
- **Auto-start** — mark tunnels as `enabled` and they connect on launch
- **Live status** — real-time Connected / Offline / Error indicators
- **Key & password auth** — supports SSH key files and password authentication

## Tech Stack

Python 3.14 · Flask · Paramiko · pystray · tomlkit

## Installation

```bash
# Clone the repository
git clone <repo-url> && cd auto-port-forward

# Install dependencies (requires uv)
uv sync
```

## Configuration

On first run a `config.toml` is created from `config.example.toml`. You can also copy it manually:

```bash
cp config.example.toml config.toml
```

Add SSH connections and tunnels:

```toml
[settings]
web_port = 9876

[ssh.myserver]
host = "myserver.example.com"
port = 22
username = "user"
key_file = "~/.ssh/id_rsa"   # or use password = "..."

[[tunnels]]
name = "Database"
ssh = "myserver"
remote_host = "localhost"
remote_port = 5432
local_port = 5432
enabled = true
```

## Usage

```bash
python main.py
```

The system tray icon appears and the web UI is available at `http://127.0.0.1:9876` (or your configured port). Click **Open UI** in the tray menu to launch it.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ssh` | List SSH connections |
| `PUT` | `/api/ssh/<name>` | Create / update a connection |
| `DELETE` | `/api/ssh/<name>` | Delete a connection |
| `GET` | `/api/tunnels` | List tunnels with status |
| `POST` | `/api/tunnels` | Create a tunnel |
| `PUT` | `/api/tunnels/<name>` | Update a tunnel |
| `DELETE` | `/api/tunnels/<name>` | Delete a tunnel |
| `POST` | `/api/tunnels/<name>/start` | Start a tunnel |
| `POST` | `/api/tunnels/<name>/stop` | Stop a tunnel |
