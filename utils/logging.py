import logging
import json
import uuid
import os
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

def get_correlation_id() -> str:
    cid = correlation_id_var.get()
    if cid is None:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging(level: str = "INFO", json_format: bool = True):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    console = logging.StreamHandler()
    if json_format:
        console.setFormatter(JSONFormatter())
    else:
        console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(console)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)