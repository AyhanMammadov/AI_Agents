from openai import OpenAI
from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.technical_writer_prompt import (
    TECHNICAL_WRITER_SYSTEM_PROMPT,
)

client = OpenAI(api_key=OPENAI_API_KEY)


def technical_writer_agent(task: str) -> str:
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": TECHNICAL_WRITER_SYSTEM_PROMPT},
            {"role": "system", "content": TECHNICAL_WRITER_REFERENCE},
            {"role": "user", "content": f"Входная задача:\n{task}"},
        ],
        temperature=0.2,
    )

    result = response.choices[0].message.content

    if not result or len(result.strip()) < 50:
        return "Ошибка: Technical Writer вернул слишком слабый ответ"

    return result