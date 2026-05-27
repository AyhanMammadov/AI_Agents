import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, STRONG_MODEL
from app.core.token_usage import record_openai_usage
from app.prompts.senior_frontend_prompt import SENIOR_FRONTEND_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)


def _normalize_files(files):
    if not isinstance(files, list) or not files:
        return None

    normalized = []

    for item in files:
        if not isinstance(item, dict):
            return None

        path = item.get("path")
        content = item.get("content")

        if not isinstance(path, str) or not path.strip():
            return None

        if not isinstance(content, str):
            return None

        normalized.append({
            "path": path.replace("\\", "/").strip(),
            "content": content,
        })

    return normalized


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
            model=STRONG_MODEL,
            messages=[
                {"role": "system", "content": SENIOR_FRONTEND_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        record_openai_usage(response, "senior_frontend", STRONG_MODEL)

        result = response.choices[0].message.content

        if not result:
            fallback["error"] = "empty response from senior_frontend"
            return fallback

        parsed = json.loads(result)

        files = _normalize_files(parsed.get("files"))
        if files is None:
            fallback["error"] = "frontend agent returned invalid files[]"
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
