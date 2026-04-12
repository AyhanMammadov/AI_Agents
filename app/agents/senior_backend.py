import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.senior_backend_prompt import SENIOR_BACKEND_SYSTEM_PROMPT

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


def senior_backend_agent(context: dict) -> dict:
    fallback = {
        "role": "senior_backend",
        "deliverables": {},
        "files": [],
        "decisions": [],
        "assumptions": [],
        "open_questions": ["Backend вернул пустой или некорректный результат"],
        "error": None,
    }

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SENIOR_BACKEND_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, indent=2),
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content

        print("\n[DEBUG][BACKEND] raw response received:", bool(result))
        print("[DEBUG][BACKEND] raw response length:", len(result) if result else 0)

        if result:
            preview = result[:500]
            print("[DEBUG][BACKEND] raw response preview:")
            print(preview)

        if not result:
            fallback["error"] = "empty response from senior_backend"
            return fallback

        parsed = json.loads(result)

        print("[DEBUG][BACKEND] parsed keys:", list(parsed.keys()))

        files = _normalize_files(parsed.get("files"))
        if files is None:
            fallback["error"] = "backend agent returned invalid files[]"
            print("[DEBUG][BACKEND] files normalization failed")
            return fallback

        print("[DEBUG][BACKEND] files count:", len(files))

        return {
            "role": "senior_backend",
            "deliverables": parsed.get("deliverables", {}),
            "files": files,
            "decisions": parsed.get("decisions", []),
            "assumptions": parsed.get("assumptions", []),
            "open_questions": parsed.get("open_questions", []),
            "error": parsed.get("error"),
        }

    except json.JSONDecodeError:
        fallback["error"] = "invalid json from senior_backend"
        print("[DEBUG][BACKEND] json decode error")
        return fallback

    except Exception as e:
        fallback["error"] = f"senior_backend failed: {str(e)}"
        print("[DEBUG][BACKEND] exception:", str(e))
        return fallback