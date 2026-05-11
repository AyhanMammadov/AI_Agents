# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Overview

This is a multi-agent AI system that accepts natural language tasks and either answers them directly, structures them as business requirements, or generates and runs complete software projects. It exposes three interfaces: a CLI (`main.py`), a FastAPI HTTP API (`api.py`), and a Telegram bot (`run_bot.py`/`app/telegram_bot.py`).

## Running the System

```bash
# Install dependencies
pip install -r requirements.txt

# CLI interactive mode
python main.py

# HTTP API server (used in production via Procfile)
uvicorn api:app --reload

# Telegram polling bot
python run_bot.py

# Initialize the database (optional, requires asyncpg not in requirements.txt)
python init_db.py
```

**Required environment variables** (in `.env` or shell):
- `OPENAI_API_KEY` — required for all LLM calls
- `TELEGRAM_BOT_TOKEN` — required for Telegram features

**Optional:**
- `CHAT_MODEL` (default: `gpt-4.1`)
- `TRANSCRIBE_MODEL` (default: `gpt-4o-mini-transcribe`)

## Architecture

### Request Flow

Every request enters through `run_system()` in `main.py`:

1. **Intent routing** — `app/agents/intent_router.py` calls GPT to classify the task into one of six intents: `simple_answer`, `business_task`, `build_project`, `edit_project`, `fix_project`, `status_request`
2. **Dispatch** — `main.py` routes to the appropriate handler. Note: `edit_project` and `fix_project` are **not implemented** and return error stubs.
3. **Build pipeline** — for `build_project`, `app/orchestrator.py` runs a sequential multi-agent pipeline.

### Build Pipeline (`build_project` mode)

`run_orchestrator()` in `app/orchestrator.py`:
1. Creates a timestamped workspace directory under `workspaces/`
2. Calls `build_route_plan()` (`app/core/router.py`) — uses keyword/phrase matching (not LLM) to determine `ProjectType` and construct a sequential list of `AgentTask`s
3. Runs each agent via `Executor` (`app/core/executor.py`) — each agent produces an `Artifact` stored in `ProjectState.artifacts` keyed by `ref`
4. Writes generated files to disk via `apply_generated_code()` (`app/core/runtime.py`)
5. Attempts to start the project via `auto_run_project()` (`app/core/auto_run.py`)

### Agent Pipeline Order

| Step | Agent (AgentName enum) | Output ref | Wrapper |
|---|---|---|---|
| 1 | `PLANNER` | `brief` | `product_owner_agent` |
| 2 | `SPEC` | `spec` | `business_analyst_agent` |
| 3 | `ARCHITECT` | `architecture` | `architect_agent` |
| 4 | `BACKEND` (if needed) | `backend_code` | `senior_backend_agent` |
| 5 | `FRONTEND` (if needed) | `frontend_code` | `senior_frontend_agent` |
| 6 | `MOBILE` (if needed) | `mobile_code` | *(not registered yet)* |
| 7 | `QA` | `test_plan` | `qa_agent` |
| 8 | `VALIDATOR` | `validation_result` | inline logic in `registry.py` |
| 9 | `DEPLOY` | `deploy_result` | stub (no real deployment) |

`AGENT_REGISTRY` in `app/agents/registry.py` maps `AgentName` → wrapper function that creates the `Artifact`.

### State

`ProjectState` (`app/core/state_store.py`) is a dataclass passed through the entire pipeline. It holds:
- `task`, `workspace`, `project_type`
- `artifacts: Dict[str, Artifact]` — all agent outputs, keyed by `ref`
- `run_history`, `decisions`, `assumptions`, `open_questions`
- `backend_retry_feedback` / `frontend_retry_feedback` — set by `Executor` to trigger one retry on contract failure

`session_store.py` stores the last `build_project` result in a **module-level global** — not persisted across restarts.

### Contract Validation & Retry

After `BACKEND` and `FRONTEND` agents run, the `Executor` checks their output against contracts:

- **Backend contract** (`app/core/backend_contract.py`): requires `main.py` with `FastAPI` + `app = FastAPI(` + `/health` endpoint, and `requirements.txt` with `fastapi`/`uvicorn`
- **Frontend contract** (`app/core/frontend_contract.py`): requires `package.json`, `index.html` (at root, not `src/`), `vite.config.js`, `src/main.jsx`, `src/App.jsx`, and correct Vite scripts (`dev`, `build`, `preview`)

If a contract fails, the `Executor` injects `backend_retry_feedback` or `frontend_retry_feedback` into `ProjectState` and re-runs the agent once. A second failure raises `ExecutionError` and halts the pipeline.

`auto_run_project()` can also trigger a **frontend runtime retry** if `npm install` or `npm run build` fails.

### Agent Implementation Pattern

Most agents follow one of two patterns:

1. **`BaseAgent` subclass** (`app/core/agent_base.py`) — constructor takes `name`, `system_prompt`, `output_schema`. `run(context)` calls OpenAI with `response_format={"type": "json_object"}` and validates against schema, returning a fallback dict on any error.

2. **Standalone function** (e.g. `senior_backend_agent`) — makes OpenAI calls directly and handles contract/retry logic inline.

All agents receive a `context: dict` built by `build_agent_context()` in `registry.py`, which populates available artifact data from `ProjectState`. Prompts live in `app/prompts/` as module-level string constants.

### Model Usage

| Model config | Default | Used by |
|---|---|---|
| `STRONG_MODEL` | `gpt-4.1` | `architect`, `senior_backend`, and other code-gen agents |
| `CHAT_MODEL` | `gpt-4.1` | `BaseAgent`, `intent_router`, most other agents |
| `CHEAP_MODEL` | `gpt-4o-mini` | Available in config, not yet used |
| `TRANSCRIBE_MODEL` | `gpt-4o-mini-transcribe` | Voice messages in Telegram bot |

### Generated Project Structure

Backend files are written to `workspaces/<name>_<timestamp>/backend/`, frontend to `.../frontend/`. The `auto_run_project()` logic:
- Backend: starts via `uvicorn main:app` and polls for port open (20s timeout)
- Frontend: runs `npm install` then `npm run build` (validation), then `npm run dev` on port 5173

**Important**: `app/core/process_runner.py` uses `cmd /c npm ...` — frontend auto-run only works on Windows. The backend startup is cross-platform.

## Key Limitations to Be Aware Of

- `edit_project` and `fix_project` intents return error stubs — they are not implemented
- The `deploy_wrapper` is a stub that always returns `url: null`
- `AgentName.MOBILE` is defined but has no registered wrapper in `AGENT_REGISTRY`
- `session_store.py` is in-memory only; restarting the server loses the last result
- `init_db.py` uses `asyncpg` which is not in `requirements.txt`
- `app.py` (root) is empty
