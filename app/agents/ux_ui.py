import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.core.token_usage import record_openai_usage
from app.prompts.ux_ui_prompt import UX_UI_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def ux_ui_agent(context: dict) -> dict:
    fallback = {
        "role": "ux_ui",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["UX/UI вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": UX_UI_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        record_openai_usage(response, "ux_ui", CHAT_MODEL)

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from ux_ui"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "ux_ui",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from ux_ui"
        return fallback

    except Exception as e:
        fallback["error"] = f"ux_ui failed: {str(e)}"
        return fallback
