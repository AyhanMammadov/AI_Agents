import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.business_analyst_prompt import BUSINESS_ANALYST_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def business_analyst_agent(context: dict) -> dict:
    fallback = {
        "role": "business_analyst",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["BA вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": BUSINESS_ANALYST_SYSTEM_PROMPT},
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
            fallback["error"] = "empty response from business_analyst"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "business_analyst",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from business_analyst"
        return fallback

    except Exception as e:
        fallback["error"] = f"business_analyst failed: {str(e)}"
        return fallback