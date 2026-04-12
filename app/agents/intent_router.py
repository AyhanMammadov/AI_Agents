import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


INTENT_ROUTER_SYSTEM_PROMPT = """
Ты AI intent router.

Твоя задача:
понять, к какому режиму относится запрос пользователя.

Ты должен вернуть JSON ТОЛЬКО в таком формате:

{
  "intent": "simple_answer",
  "reason": "почему ты так решил",
  "confidence": 0.95
}

Разрешённые значения intent:

1. simple_answer
Используй если:
- пользователь задаёт обычный вопрос
- хочет объяснение
- хочет короткий ответ
- не просит создать или изменить проект

2. business_task
Используй если:
- пользователь просит user story
- tasks
- acceptance criteria
- task description
- бизнес-структурирование
- описание задачи для команды
- декомпозицию

3. build_project
Используй если:
- пользователь просит создать новый проект
- сделать backend / frontend / fullstack / app / bot
- сгенерировать рабочий код
- создать приложение с нуля

4. edit_project
Используй если:
- пользователь хочет изменить уже созданный проект
- добавить новую фичу в существующий проект
- изменить UI
- доработать текущий проект
- продолжить уже созданный проект

5. fix_project
Используй если:
- пользователь просит исправить ошибку
- починить баг
- исправить код
- устранить проблему
- решить traceback / exception / crash

6. status_request
Используй если:
- пользователь спрашивает статус
- что уже сделано
- где файлы
- где проект
- какой workspace
- что с результатом
- что уже готово

Правила:
- Всегда возвращай только JSON
- Не придумывай новые intent
- Если сомневаешься между simple_answer и build_project:
  выбери simple_answer, если пользователь не просит код или проект явно
- Если сомневаешься между edit_project и fix_project:
  edit_project = доработка / изменение
  fix_project = ошибка / поломка / bug / crash
"""


def ai_intent_router(task: str) -> dict:
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": INTENT_ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        intent = parsed.get("intent")
        reason = parsed.get("reason", "")
        confidence = parsed.get("confidence", 0)

        allowed = {
            "simple_answer",
            "business_task",
            "build_project",
            "edit_project",
            "fix_project",
            "status_request",
        }

        if intent not in allowed:
            return {
                "error": f"Invalid intent returned: {intent}",
                "raw": parsed,
            }

        return {
            "intent": intent,
            "reason": reason,
            "confidence": confidence,
        }

    except Exception as e:
        return {
            "error": str(e),
        }