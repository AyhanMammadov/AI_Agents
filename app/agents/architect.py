import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, STRONG_MODEL
from app.core.token_usage import record_openai_usage
from app.prompts.architect_prompt import ARCHITECT_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def architect_agent(context: dict) -> dict:
    fallback = {
        "role": "architect",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["Architect вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=STRONG_MODEL,
            messages=[
                {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        record_openai_usage(response, "architect", STRONG_MODEL)

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from architect"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "architect",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from architect"
        return fallback

    except Exception as e:
        fallback["error"] = f"architect failed: {str(e)}"
        return fallback
