import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.senior_frontend_prompt import SENIOR_FRONTEND_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def senior_frontend_agent(context: dict) -> dict:
    fallback = {
        "role": "senior_frontend",
        "deliverables": {},
        "files": [],
        "decisions": [],
        "assumptions": [],
        "open_questions": ["Frontend вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SENIOR_FRONTEND_SYSTEM_PROMPT},
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
            fallback["error"] = "empty response from senior_frontend"
            return fallback

        parsed = json.loads(result)

        files = parsed.get("files", [])
        if not isinstance(files, list):
            fallback["error"] = "frontend agent returned invalid files format"
            return fallback

        return {
            "role": "senior_frontend",
            "deliverables": parsed.get("deliverables", {}),
            "files": files,
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from senior_frontend"
        return fallback

    except Exception as e:
        fallback["error"] = f"senior_frontend failed: {str(e)}"
        return fallback