from app.core.agent_base import BaseAgent
from app.prompts.business_analyst_prompt import BUSINESS_ANALYST_SYSTEM_PROMPT


BUSINESS_ANALYST_OUTPUT_SCHEMA = {
    "deliverables": {},
    "decisions": [],
    "assumptions": [],
    "open_questions": [],
}


def business_analyst_agent(context: dict) -> dict:
    agent = BaseAgent(
        name="business_analyst",
        system_prompt=BUSINESS_ANALYST_SYSTEM_PROMPT,
        output_schema=BUSINESS_ANALYST_OUTPUT_SCHEMA,
    )
    return agent.run(context)