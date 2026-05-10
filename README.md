# Apna AI Agent

An autonomous AI Agent platform that executes real-world tasks in a built-in browser and cloud desktop environment. Give it a command like *"Build an Android app and upload to GitHub"* — the agent plans, codes, and deploys while you watch live.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile / Web UI                          │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │   Chat Interface     │  │   Live Desktop/Browser Stream    │ │
│  │   (command input)    │  │   (noVNC / WebSocket frames)     │ │
│  └──────────┬───────────┘  └──────────────┬───────────────────┘ │
└─────────────┼─────────────────────────────┼─────────────────────┘
              │ REST / WebSocket            │ WebSocket
              ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Orchestrator (FastAPI)                │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   Planner  │  │ Task Manager │  │   Stream Manager         │ │
│  │  (LLM →   │  │ (queue,      │  │   (screenshot frames →   │ │
│  │   steps)   │  │  lifecycle)  │  │    WebSocket broadcast)  │ │
│  └─────┬──────┘  └──────┬───────┘  └──────────────────────────┘ │
│        │                │                                       │
│  ┌─────▼────────────────▼───────────────────────────────────┐   │
│  │              Agent Orchestrator                           │   │
│  │  plan → observe → decide → act → repeat                  │   │
│  └──────────┬────────────────────────────┬──────────────────┘   │
│             │                            │                      │
│  ┌──────────▼──────────┐    ┌────────────▼───────────────────┐  │
│  │  Ollama LLM Client  │    │  Playwright Browser Controller │  │
│  │  (Llama 3.1 / Qwen) │    │  (navigate, click, type, DOM) │  │
│  └─────────────────────┘    └────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────┐                                        │
│  │  Credential Vault   │  (Fernet-encrypted SQLite)             │
│  └─────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
              │
              │ Docker Network
              ▼
┌─────────────────────────────────────────────────────────────────┐
│               Virtual Desktop Container                         │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  XFCE 4    │  │  Chrome  │  │  VS Code │  │ Android SDK  │  │
│  │  Desktop   │  │          │  │ (server) │  │ (CLI tools)  │  │
│  └────────────┘  └──────────┘  └──────────┘  └──────────────┘  │
│  ┌────────────┐  ┌──────────┐                                   │
│  │  TigerVNC  │  │  noVNC   │  (web-based VNC client)           │
│  └────────────┘  └──────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ollama Container                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Local LLM: Llama 3.1 (8B) / Qwen 2.5-Coder / etc.     │   │
│  │  Free, self-hosted, no API keys required                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Zero-Cost Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| **AI Brain** | Ollama + Llama 3.1 (8B/70B) or Qwen 2.5-Coder | Free (self-hosted) |
| **Browser Engine** | Playwright (Chromium) | Free (open-source) |
| **Desktop Env** | Docker + XFCE + TigerVNC | Free (open-source) |
| **Streaming** | noVNC + WebSocket | Free (open-source) |
| **Backend** | FastAPI (Python) | Free (open-source) |
| **Hosting** | Oracle Cloud Free Tier / Google Cloud Free Trial | Free tier |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM (for Ollama with Llama 3.1 8B)
- 20GB+ disk space

### 1. Clone and configure
```bash
git clone https://github.com/ziaullahKhalid/Apna-ai-agent.git
cd Apna-ai-agent
cp .env.example .env
# Edit .env to customize settings
```

### 2. Start all services
```bash
docker compose up -d
```

### 3. Pull the LLM model
```bash
# Default: Llama 3.1 8B
docker compose exec ollama ollama pull llama3.1:8b

# Alternative: Qwen 2.5-Coder (better for coding tasks)
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

### 4. Access the platform
| Service | URL | Description |
|---------|-----|-------------|
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Desktop** | http://localhost:6080 | noVNC web desktop |
| **VS Code** | http://localhost:8443 | Code editor |
| **Ollama** | http://localhost:11434 | LLM API |

## API Usage

### Submit a task
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"command": "Go to GitHub and create a new repository called my-project"}'
```

### Watch task progress (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks/{task_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event, data);
};
```

### Live browser stream (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'frame') {
    // data.data is base64-encoded JPEG
    img.src = 'data:image/jpeg;base64,' + data.data;
  }
};

// Send human input (when in manual control mode)
ws.send(JSON.stringify({ type: 'mouse_click', x: 100, y: 200 }));
ws.send(JSON.stringify({ type: 'keyboard', key: 'Enter' }));
```

### Human-in-the-loop
```bash
# Enable manual control (agent pauses)
curl -X POST http://localhost:8000/api/v1/browser/human-control/enable

# Disable manual control (agent resumes)
curl -X POST http://localhost:8000/api/v1/browser/human-control/disable

# Provide input for CAPTCHA/2FA
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/human-input \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"captcha_solved": true}}'
```

### Credential vault
```bash
# Store credentials
curl -X POST http://localhost:8000/api/v1/vault/credentials \
  -H "Content-Type: application/json" \
  -d '{"service": "github", "username": "myuser", "credentials": {"password": "..."}}'

# List stored services
curl http://localhost:8000/api/v1/vault/services
```

## Key Features

### Integrated Browser (Playwright)
- Full DOM parsing and accessibility tree extraction
- Coordinate-based clicking for complex UIs
- Screenshot capture at configurable FPS
- Interactive element detection and labeling
- Human takeover mode for CAPTCHAs and 2FA

### Autonomous Coding & Deployment
- Git operations (clone, commit, push)
- Code editing via VS Code (code-server)
- Android SDK for mobile app compilation
- Terminal access in cloud desktop

### Credential Vault
- AES-128 Fernet encryption at rest
- SQLite-backed with key separation
- Per-service credential storage
- No plaintext secrets on disk

### Live Streaming
- WebSocket-based JPEG frame streaming
- Configurable FPS (default 10) and quality
- Touch/click/keyboard input forwarding
- Event notifications for task progress

## Hosting Recommendations (Free Tier)

### Oracle Cloud (Always Free)
- **VM.Standard.A1.Flex**: 4 OCPUs, 24GB RAM (ARM)
- Perfect for running Ollama + Desktop container
- Guide: [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)

### Google Cloud (Free Trial)
- $300 credit for 90 days
- **e2-standard-4**: 4 vCPUs, 16GB RAM
- Guide: [Google Cloud Free Trial](https://cloud.google.com/free)

### Self-Hosted (Home Server)
- Any machine with 8GB+ RAM
- Docker + Docker Compose installed
- Port forwarding for remote access

## Project Structure

```
agent-platform/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── orchestrator.py    # Main agent loop
│   │   │   ├── task_manager.py    # Task queue & lifecycle
│   │   │   └── planner.py        # LLM-based task decomposition
│   │   ├── browser/
│   │   │   ├── controller.py      # Playwright browser control
│   │   │   ├── dom_parser.py      # DOM/accessibility parsing
│   │   │   └── actions.py         # Action primitives
│   │   ├── llm/
│   │   │   ├── ollama_client.py   # Ollama REST client
│   │   │   └── prompts.py        # System prompts
│   │   ├── vault/
│   │   │   └── credential_store.py # Encrypted credential storage
│   │   ├── streaming/
│   │   │   └── stream_manager.py  # WebSocket frame streaming
│   │   ├── api/
│   │   │   ├── routes.py         # REST endpoints
│   │   │   └── websocket.py      # WebSocket handlers
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   └── main.py               # FastAPI entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── desktop/
│   ├── Dockerfile                # Ubuntu + VNC + noVNC + tools
│   ├── supervisord.conf          # Process manager config
│   └── startup.sh               # Desktop init script
├── docker-compose.yml            # Full stack orchestration
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Development

### Run backend locally (without Docker)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Start Ollama separately: ollama serve
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run tests
```bash
cd backend
pip install -e ".[dev]"
pytest
```

## License

Open-source for educational and personal use.
