import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.product_owner_prompt import PRODUCT_OWNER_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def product_owner_agent(context: dict) -> dict:
    fallback = {
        "role": "product_owner",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["Product Owner вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": PRODUCT_OWNER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, indent=2),
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from product_owner"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "product_owner",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from product_owner"
        return fallback

    except Exception as e:
        fallback["error"] = f"product_owner failed: {str(e)}"
        return fallback