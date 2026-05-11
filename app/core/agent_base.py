import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, output_schema: dict):
        self.name = name
        self.system_prompt = system_prompt
        self.output_schema = output_schema

    def _build_fallback(self, error_message: str) -> dict:
        fallback = {"role": self.name, "error": error_message}

        for key, default_value in self.output_schema.items():
            fallback[key] = default_value

        return fallback

    def _validate_result(self, result: dict) -> dict:
        if not isinstance(result, dict):
            raise ValueError("agent result is not a JSON object")

        validated = {}

        for key, default_value in self.output_schema.items():
            validated[key] = result.get(key, default_value)

        validated["role"] = self.name
        validated["error"] = result.get("error")

        return validated

    def run(self, context: dict) -> dict:
        try:
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(context, ensure_ascii=False),
                    },
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            if not content:
                return self._build_fallback("empty response")

            parsed = json.loads(content)
            return self._validate_result(parsed)

        except json.JSONDecodeError:
            return self._build_fallback("invalid json")
        except Exception as e:
            return self._build_fallback(f"{self.name} failed: {str(e)}")