# NEXA — Agentic AI Personal OS Assistant

> An intelligent AI agent that understands your goals and autonomously executes multi-step tasks across your operating system, applications, browser, and files.

## Architecture

```
nexa/
├── frontend/          # Flutter desktop application
│   └── nexa_app/
├── backend/           # Python FastAPI backend
│   └── app/
│       ├── agent/     # Agent core (planner, executor, observer, verifier)
│       ├── ai/        # LLM provider abstraction layer
│       ├── api/       # WebSocket & REST handlers
│       ├── memory/    # Context & preference management
│       ├── security/  # Permissions, audit, emergency stop
│       └── tools/     # Universal tool system
│           ├── browser/
│           ├── computer/
│           ├── filesystem/
│           └── os_tools/
├── tests/             # Test suite
└── docs/              # Documentation
```

## Quick Start

### Prerequisites
- Python 3.12+
- Flutter 3.x+ with Windows desktop support
- At least one LLM API key (OpenAI, Gemini, Anthropic, or local Ollama)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Configure environment
copy ..\.env.example .env
# Edit .env with your API keys

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend/nexa_app
flutter pub get
flutter run -d windows
```

## Supported LLM Providers

| Provider | Model | Config Key |
|----------|-------|-----------|
| OpenAI | GPT-4o, GPT-4 | `OPENAI_API_KEY` |
| Google | Gemini Pro | `GEMINI_API_KEY` |
| Anthropic | Claude 3.5 | `ANTHROPIC_API_KEY` |
| Ollama | Any local model | `OLLAMA_BASE_URL` |

## First Milestone Capabilities

- Natural language goal → multi-step autonomous execution
- Screenshot capture & screen reading
- Filesystem search, read, create, organize
- Application launch, focus, management
- Browser automation (search, navigate, interact)
- System monitoring (CPU, RAM, network, processes)
- Real-time task progress visualization
- Permission-based security with user confirmations
- Emergency stop

## License

MIT
