import re
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TemplateEngine:
    def __init__(self):
        self.pattern = re.compile(r'\{\{(.+?)\}\}')

    def render(self, template: str, context: Dict[str, Any]) -> str:
        def replacer(match):
            expr = match.group(1).strip()
            try:
                value = self._evaluate_expression(expr, context)
                if value is None:
                    logger.warning(f"Template expression '{expr}' evaluated to None, using empty string.")
                    return ''
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return str(value)
            except Exception as e:
                logger.error(f"Error evaluating template expression '{expr}': {e}")
                return match.group(0)
        return self.pattern.sub(replacer, template)

    def _evaluate_expression(self, expr: str, context: Dict[str, Any]) -> Any:
        parts = [p.strip() for p in expr.split('.') if p.strip()]
        if not parts:
            return None
        current = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
            if current is None:
                return None
        return current


template_engine = TemplateEngine()