from app.core.agent_base import BaseAgent
from app.prompts.product_owner_prompt import PRODUCT_OWNER_SYSTEM_PROMPT


PRODUCT_OWNER_OUTPUT_SCHEMA = {
    "deliverables": {},
    "decisions": [],
    "assumptions": [],
    "open_questions": [],
}


def product_owner_agent(context: dict) -> dict:
    agent = BaseAgent(
        name="product_owner",
        system_prompt=PRODUCT_OWNER_SYSTEM_PROMPT,
        output_schema=PRODUCT_OWNER_OUTPUT_SCHEMA,
    )
    return agent.run(context)