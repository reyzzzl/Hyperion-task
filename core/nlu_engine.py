import json
import logging
from typing import Dict
import ollama

logger = logging.getLogger("NLUEngine")


class NLUEngine:
    def __init__(self, model: str = "mistral", backend: str = "ollama"):
        self.model = model
        self.backend = backend
        self.client = ollama.AsyncClient()
        self.intent_schema = {
            "create_order": {"description": "Create a new sales order", "params": ["customer", "product", "quantity"]},
            "check_status": {"description": "Check order or ticket status", "params": ["order_id"]},
            "send_email": {"description": "Send an email", "params": ["to", "subject", "body"]},
            "update_crm": {"description": "Update CRM lead status", "params": ["lead_id", "status"]},
            "create_ticket": {"description": "Create support ticket", "params": ["customer_email", "issue"]},
            "unknown": {"description": "Unknown intent, needs clarification", "params": []},
        }

    def build_nlu_prompt(self, user_input: str) -> str:
        schema_str = json.dumps(self.intent_schema, indent=2)
        return (
            "You are a strict natural language understanding engine. "
            "Your only task is to classify the user's intent and extract parameters. "
            f"Available intents and their parameters:\n{schema_str}\n\n"
            "User input: " + user_input + "\n\n"
            "Respond with a single JSON object:\n"
            "{'intent': '<intent_name>', 'params': {<extracted_parameters>}, 'confidence': <0.0-1.0>}\n"
            "Only the JSON. No markdown, no extra text."
        )

    async def parse_intent(self, user_input: str) -> Dict:
        if self.backend == "ollama":
            try:
                response = await self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": self.build_nlu_prompt(user_input)}],
                    format="json",
                )
                
                content = response.message.content.strip()
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != 0:
                        try:
                            parsed = json.loads(content[json_start:json_end])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to extract JSON from NLU response: {content}")
                            return {"intent": "unknown", "params": {}, "confidence": 0.0}
                    else:
                        logger.error(f"NLU response is not valid JSON: {content}")
                        return {"intent": "unknown", "params": {}, "confidence": 0.0}
                intent = parsed.get("intent", "unknown")
                params = parsed.get("params", {})
                confidence = parsed.get("confidence", 0.0)
                if confidence < 0.7:
                    intent = "unknown"
                    params = {}
                return {"intent": intent, "params": params, "confidence": confidence}
            except Exception as e:
                logger.error(f"NLU error: {e}")
        return {"intent": "unknown", "params": {}, "confidence": 0.0}
