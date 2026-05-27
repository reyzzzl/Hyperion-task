import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
import msal

logger = logging.getLogger("Microsoft365")


class Microsoft365:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=self.authority,
            client_credential=client_secret
        )
        self.token = None
        self.token_expiry = datetime.now()
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self._acquire_token()

    def _acquire_token(self):
        result = self.app.acquire_token_silent(self.scope, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        if "access_token" in result:
            self.token = result['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=result.get('expires_in', 3600) - 60)
        else:
            error_desc = result.get('error_description', 'Unknown error')
            logger.error(f"MS365 auth failed: {error_desc}")
            raise ConnectionError(f"Microsoft 365 authentication failed: {error_desc}")

    def _ensure_token(self):
        if not self.token or datetime.now() >= self.token_expiry:
            self._acquire_token()

    async def send_email(self, to: str, subject: str, body: str) -> Dict:
        self._ensure_token()
        if not self.token:
            return {"success": False, "error": "No valid token"}
        endpoint = f"{self.graph_url}/users/admin@{self.tenant_id}/sendMail"
        email_msg = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}]
            }
        }
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(endpoint, headers=headers, json=email_msg)
            if resp.status_code == 401:
                self._acquire_token()
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                    resp = await client.post(endpoint, headers=headers, json=email_msg)
            return {"success": resp.status_code == 202, "status_code": resp.status_code}

    async def create_teams_meeting(self, subject: str, start_time: str, end_time: str, attendees: List[str]) -> Dict:
        self._ensure_token()
        if not self.token:
            return {"success": False, "error": "No valid token"}
        endpoint = f"{self.graph_url}/users/admin@{self.tenant_id}/calendar/events"
        event = {
            "subject": subject,
            "start": {"dateTime": start_time, "timeZone": "Asia/Jakarta"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Jakarta"},
            "attendees": [{"emailAddress": {"address": e}} for e in attendees],
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness"
        }
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(endpoint, headers=headers, json=event)
            if resp.status_code == 401:
                self._acquire_token()
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                    resp = await client.post(endpoint, headers=headers, json=event)
            if resp.status_code == 201:
                data = resp.json()
                join_url = data.get('onlineMeeting', {}).get('joinUrl', '')
                return {"success": True, "event_id": data['id'], "teams_link": join_url}
            return {"success": False, "error": resp.text}