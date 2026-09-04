# DashCraft ⚡

DashCraft is a lightweight, zero-dependency frontend dashboard for real-time host hardware monitoring (CPU, RAM, Disk) and Minecraft Java server status tracking with interactive RCON console support.

![License: AGPLv3](https://img.shields.io/badge/License-AGPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)

---

## Technical Architecture

┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│   Chart.js UI  ◄─── WebSocket (JSON Streams) ───►  RCON Terminal│
└──────────────────────────────▲──────────────────────────────┘
                               │
                       ws://localhost:8000/ws
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    DashCraft Backend                        │
│                   (FastAPI + Uvicorn)                       │
├──────────────────────────────┬──────────────────────────────┤
│  psutil System Collector     │  mcstatus & MCRcon Client    │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
         System APIs                    Minecraft Server
       (CPU, RAM, Disk)               (Port 25565 / RCON 25575)

```

---

## Directory Layout

```text
dashcraft/
├── app.py             # FastAPI server, WebSocket broadcaster, RCON client
├── index.html         # Single-page dashboard UI with Chart.js & WebSockets
├── .env               # Active configuration parameters
├── .env.example       # Template configuration file
├── requirements.txt   # Python dependencies
└── LICENSE            # AGPLv3 License file

```

---

## Quickstart Guide

### 1. Requirements

* **Python**: `3.8` or higher
* **Minecraft Java Server**: Requires Query/Status enabled (default) and RCON enabled for terminal commands.

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone [https://github.com/your-username/dashcraft.git](https://github.com/your-username/dashcraft.git)
cd dashcraft
pip install -r requirements.txt

```

### 3. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env

```

---

## Detailed Configuration (.env)

Edit the `.env` file according to your setup:

```ini
# ==============================================================================
# Web Server Configuration
# ==============================================================================

# Bind address for FastAPI (0.0.0.0 exposes to LAN, 127.0.0.1 for local-only)
HOST=0.0.0.0

# HTTP Port for the dashboard
PORT=8000

# Automatically open the web browser tab when python app.py is run
AUTO_OPEN_BROWSER=true


# ==============================================================================
# Minecraft Server Targets
# ==============================================================================

# IP address or domain name of your Minecraft server
MC_SERVER_IP=127.0.0.1

# Server primary query port (default: 25565)
MC_SERVER_PORT=25565


# ==============================================================================
# Minecraft RCON Settings
# ==============================================================================

# Toggle RCON terminal capability in the UI (true / false)
RCON_ENABLED=true

# RCON listening port (default: 25575)
RCON_PORT=25575

# RCON authentication password (must match server.properties)
RCON_PASSWORD=my_secure_rcon_password

```

---

## Minecraft Server Setup (`server.properties`)

To enable full status reporting and the interactive RCON terminal, edit your Minecraft server's `server.properties` file:

```ini
enable-rcon=true
rcon.port=25575
rcon.password=my_secure_rcon_password
broadcast-rcon-to-ops=true
enable-query=true
query.port=25565

```

> **Note:** Restart your Minecraft server after changing `server.properties`.

---

## Execution

Run the backend script:

```bash
python app.py

```

* If `AUTO_OPEN_BROWSER=true`, your default browser will launch at `http://localhost:8000`.
* If hosting remotely, navigate directly to `http://<YOUR_SERVER_IP>:8000`.

---

## API & WebSocket Specification

### WebSocket Endpoint: `/ws`

#### 1. Outgoing Metrics Payload (Server ➔ Client every 1.5s)

```json
{
  "type": "metrics",
  "system": {
    "cpu": 12.5,
    "ram": 48.2,
    "disk": 65.0
  },
  "minecraft": {
    "online": true,
    "players_online": 3,
    "players_max": 20,
    "latency": 14.2,
    "version": "1.20.4",
    "players_list": ["Steve", "Alex", "Notch"]
  }
}

```

#### 2. Incoming RCON Request Payload (Client ➔ Server)

```json
{
  "action": "rcon_command",
  "command": "say Hello from DashCraft!"
}

```

#### 3. Outgoing RCON Response Payload (Server ➔ Client)

```json
{
  "type": "rcon_response",
  "command": "say Hello from DashCraft!",
  "response": "[Server] Hello from DashCraft!"
}

```

---

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| **Server status shows "Offline"** | Wrong IP/Port or firewalled | Verify `MC_SERVER_IP` and `MC_SERVER_PORT` in `.env`. Ensure port 25565 is open. |
| **RCON returns "Connection Refused"** | RCON is disabled or port blocked | Ensure `enable-rcon=true` in `server.properties` and `RCON_PORT` is open. |
| **Browser doesn't open automatically** | System headless or setting disabled | Set `AUTO_OPEN_BROWSER=true` in `.env` or navigate to `http://localhost:8000` manually. |

---

## License

Distributed under the **GNU Affero General Public License v3.0 (AGPLv3)**. See `LICENSE` for details.
