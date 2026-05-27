import os
import secrets
import logging

logger = logging.getLogger(__name__)

API_TOKEN = os.environ.get("DASHBOARD_API_TOKEN")
if not API_TOKEN:
    API_TOKEN = secrets.token_urlsafe(32)
    logger.critical("DASHBOARD_API_TOKEN not set. Generated random token: %s. Set this in environment for persistence.", API_TOKEN)