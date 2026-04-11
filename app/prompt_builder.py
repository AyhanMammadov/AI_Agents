def build_prompt(global_rules, role_prompt, context):
    return f"""
{global_rules}

{role_prompt}

CONTEXT:
{context}
"""