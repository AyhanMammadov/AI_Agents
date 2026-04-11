import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.devops_prompt import (
    DEVOPS_SYSTEM_PROMPT,
)

client = OpenAI(api_key=OPENAI_API_KEY)


def devops_agent(context: dict) -> dict:
    fallback = {
        "role": "devops",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["DevOps вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": DEVOPS_SYSTEM_PROMPT},
                {"role": "system", "content": DEVOPS_REFERENCE},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, indent=2),
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from devops"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "devops",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from devops"
        return fallback

    except Exception as e:
        fallback["error"] = f"devops failed: {str(e)}"
        return fallback