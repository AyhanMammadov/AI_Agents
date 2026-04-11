import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.qa_prompt import QA_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def qa_agent(context: dict) -> dict:
    fallback = {
        "role": "qa",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["QA вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT},
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
            fallback["error"] = "empty response from qa"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "qa",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from qa"
        return fallback

    except Exception as e:
        fallback["error"] = f"qa failed: {str(e)}"
        return fallback