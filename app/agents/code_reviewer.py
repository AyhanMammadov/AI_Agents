import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.core.token_usage import record_openai_usage
from app.prompts.code_reviewer_prompt import CODE_REVIEWER_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def code_reviewer_agent(context: dict) -> dict:
    fallback = {
        "role": "code_reviewer",
        "deliverables": {},
        "decisions": [],
        "assumptions": [],
        "open_questions": ["Code Reviewer вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": CODE_REVIEWER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        record_openai_usage(response, "code_reviewer", CHAT_MODEL)

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from code reviewer"
            return fallback

        parsed = json.loads(result)

        return {
            "role": "code_reviewer",
            "deliverables": parsed.get("deliverables", parsed),
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from code reviewer"
        return fallback

    except Exception as e:
        fallback["error"] = f"code_reviewer failed: {str(e)}"
        return fallback
