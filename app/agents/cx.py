import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.cx_prompt import CX_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def cx_agent(context: dict) -> dict:
    fallback = {
        "role": "cx",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["CX вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": CX_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, indent=2),
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from cx"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "cx",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from cx"
        return fallback

    except Exception as e:
        fallback["error"] = f"cx failed: {str(e)}"
        return fallback