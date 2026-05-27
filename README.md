# AI Agents Telegram Orchestrator

Telegram-first AI agent system for routing requests to the smallest useful set of agents.

## What It Does

- Answers simple questions with a single LLM call.
- Turns analysis or business requests into structured answers without waking code agents.
- Builds runnable project demos only when the user explicitly asks for an app/project.
- For mobile app requests, MVP output is a clickable React/Vite mobile-style web demo.
- Mobile demos use a lean pipeline: Product Owner -> UX/UI -> Frontend -> Validator.
- Starts generated demos locally and prepares frontend demos for Railway deployment.
- If generated frontend code fails contract/runtime validation twice, a deterministic fallback mobile demo is used so the user still gets a clickable result.
- Returns OpenAI token usage in the final result when the SDK provides usage data.
- Restricts Telegram access to configured user IDs.

## Architecture

```text
Telegram/API
  -> fast intent router
  -> main orchestrator
  -> selected agents only
  -> generated workspace
  -> local preview
  -> optional Railway deploy
```

The default orchestration mode is `fast`, which uses deterministic routing to save tokens. Set `ORCHESTRATOR_MODE=llm` only if you want the LLM to choose the build pipeline.

## Setup

```bash
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env`:

```env
OPENAI_API_KEY=your_openai_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ALLOWED_TELEGRAM_USER_IDS=123456789
```

To get your Telegram user ID, send a message to `@userinfobot` or log `update.effective_user.id` once locally.

## Run

CLI:

```bash
py main.py
```

API:

```bash
py -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

Telegram polling bot:

```bash
py run_bot.py
```

## Railway Preview Deploy

Generated frontend demos include `railway.json`.

Default behavior does not deploy automatically. To enable local Railway CLI deployment:

```env
RAILWAY_DEPLOY_ENABLED=true
RAILWAY_SERVICE_NAME=your_service_name
RAILWAY_PUBLIC_URL=https://your-service.up.railway.app
```

Then install/login/link Railway CLI in the generated frontend workspace. The app will call:

```bash
railway up --detach
```

If `RAILWAY_PUBLIC_URL` is set, the bot includes it in the reply.

## Token Saving Defaults

- Rule-based router runs before LLM routing.
- Intent routing uses `CHEAP_MODEL`.
- `CHAT_MODEL` defaults to `CHEAP_MODEL`.
- Code generation agents use `STRONG_MODEL`.
- Build orchestration defaults to deterministic `ORCHESTRATOR_MODE=fast`.

## Important Notes

- `edit_project` and `fix_project` are still stubs.
- Generated code is written under `workspaces/`.
- Generated frontend demos are React/Vite projects, including mobile-style demos.
- Do not expose `/run` publicly without `API_RUN_TOKEN`.
