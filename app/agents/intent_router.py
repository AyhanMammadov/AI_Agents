import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.intent_router_prompt import INTENT_ROUTER_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def ai_intent_router(task: str) -> dict:
    fallback = {
        "intent": None,
        "reason": "AI intent router returned invalid result",
        "confidence": 0.0,
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": INTENT_ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        if not content:
            fallback["error"] = "empty response from ai_intent_router"
            return fallback

        parsed = json.loads(content)

        intent = parsed.get("intent")

        allowed_intents = {
            "build_project",
            "task_breakdown",
            "spec_only",
            "architecture_design",
            "write_description",
            "analyze_problem",
            "explain",
            "consultation",
        }

        if intent not in allowed_intents:
            fallback["error"] = "invalid intent from ai_intent_router"
            return fallback

        return {
            "intent": intent,
            "reason": parsed.get("reason", ""),
            "confidence": parsed.get("confidence", 0.0),
            "error": None,
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from ai_intent_router"
        return fallback

    except Exception as e:
        fallback["error"] = f"ai_intent_router failed: {str(e)}"
        return fallback