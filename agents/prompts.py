CLASSIFICATION_PROMPT = """Classify the user request into one of these agent categories: {agents}
User request: {text}
Respond with ONLY the agent name (one word: {keys}).
If unsure, respond with 'executive'."""

DECISION_PROMPT = """As CEO, make a strategic decision based on:
Situation: {situation}
Sub-agent advices: {advices}
Return JSON: decision, rationale, action_items, risk_assessment."""

EXECUTIVE_FALLBACK = """As an Executive, handle: {description}
Provide high-level guidance."""