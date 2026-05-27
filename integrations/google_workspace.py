import os
import pickle
import asyncio
import base64
import uuid
import logging
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("GoogleWorkspace")


class GoogleWorkspace:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/calendar'
    ]

    def __init__(self):
        self.creds = None
        self.services = {}
        self._authenticate()

    def _authenticate(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh Google API token: {e}")
                    self.creds = None
                    raise
            else:
                if not os.path.exists('credentials.json'):
                    logger.error("credentials.json not found for Google Workspace authentication.")
                    raise FileNotFoundError("Google API credentials file 'credentials.json' not found.")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                try:
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Failed to run local server for Google API authentication: {e}")
                    raise RuntimeError("Google API authentication flow failed.") from e
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        self.services['gmail'] = build('gmail', 'v1', credentials=self.creds)
        self.services['drive'] = build('drive', 'v3', credentials=self.creds)
        self.services['sheets'] = build('sheets', 'v4', credentials=self.creds)
        self.services['docs'] = build('docs', 'v1', credentials=self.creds)
        self.services['calendar'] = build('calendar', 'v3', credentials=self.creds)

    async def send_email(self, to: str, subject: str, body: str, cc: List[str] = None, bcc: List[str] = None) -> Dict:
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            message.attach(MIMEText(body, 'html'))
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            loop = asyncio.get_running_loop()
            sent = await loop.run_in_executor(
                None,
                lambda: self.services['gmail'].users().messages().send(userId='me', body={'raw': raw}).execute()
            )
            return {"success": True, "message_id": sent['id']}
        except HttpError as error:
            logger.error(f"Gmail send error: {error}")
            return {"success": False, "error": str(error)}

    async def read_emails(self, query: str = "is:unread", max_results: int = 10) -> List[Dict]:
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.services['gmail'].users().messages().list(
                    userId='me', q=query, maxResults=max_results
                ).execute()
            )
            messages = results.get('messages', [])
            emails = []
            for msg in messages:
                email_data = await loop.run_in_executor(
                    None,
                    lambda m=msg: self.services['gmail'].users().messages().get(
                        userId='me', id=m['id'], format='full'
                    ).execute()
                )
                headers = email_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                emails.append({
                    'id': msg['id'],
                    'thread_id': email_data.get('threadId', ''),
                    'subject': subject,
                    'from': sender,
                    'snippet': email_data.get('snippet', '')
                })
            return emails
        except HttpError as error:
            logger.error(f"Gmail read error: {error}")
            return []

    async def mark_as_read(self, msg_id: str) -> Dict:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self.services['gmail'].users().messages().modify(
                    userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
                ).execute()
            )
            return {"success": True}
        except HttpError as error:
            logger.error(f"Gmail mark read error: {error}")
            return {"success": False, "error": str(error)}

    async def sheets_operation(self, spreadsheet_id: str, range_name: str, values: List[List] = None, operation: str = 'read') -> Dict:
        try:
            loop = asyncio.get_running_loop()
            if operation == 'read':
                result = await loop.run_in_executor(
                    None,
                    lambda: self.services['sheets'].spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id, range=range_name
                    ).execute()
                )
                return {"values": result.get('values', [])}
            elif operation == 'write':
                body = {'values': values}
                await loop.run_in_executor(
                    None,
                    lambda: self.services['sheets'].spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id, range=range_name,
                        valueInputOption='USER_ENTERED', body=body
                    ).execute()
                )
                return {"success": True}
            elif operation == 'append':
                body = {'values': values}
                await loop.run_in_executor(
                    None,
                    lambda: self.services['sheets'].spreadsheets().values().append(
                        spreadsheetId=spreadsheet_id, range=range_name,
                        valueInputOption='USER_ENTERED', body=body
                    ).execute()
                )
                return {"success": True}
        except HttpError as error:
            return {"success": False, "error": str(error)}

    async def create_doc(self, title: str, content: str) -> Dict:
        try:
            loop = asyncio.get_running_loop()
            doc = await loop.run_in_executor(
                None,
                lambda: self.services['docs'].documents().create(body={'title': title}).execute()
            )
            requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
            await loop.run_in_executor(
                None,
                lambda: self.services['docs'].documents().batchUpdate(
                    documentId=doc['documentId'], body={'requests': requests}
                ).execute()
            )
            return {"success": True, "document_id": doc['documentId']}
        except HttpError as error:
            return {"success": False, "error": str(error)}

    async def schedule_meeting(self, summary: str, start_time: str, end_time: str, attendees: List[str], timezone: str = None) -> Dict:
        if timezone is None:
            timezone = os.environ.get("TIMEZONE", "UTC")
        try:
            event = {
                'summary': summary,
                'start': {'dateTime': start_time, 'timeZone': timezone},
                'end': {'dateTime': end_time, 'timeZone': timezone},
                'attendees': [{'email': e} for e in attendees],
                'conferenceData': {
                    'createRequest': {
                        'requestId': str(uuid.uuid4()),
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }
            loop = asyncio.get_running_loop()
            created = await loop.run_in_executor(
                None,
                lambda: self.services['calendar'].events().insert(
                    calendarId='primary', body=event, conferenceDataVersion=1
                ).execute()
            )
            meet_link = created.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
            return {"success": True, "event_id": created['id'], "meet_link": meet_link}
        except HttpError as error:
            return {"success": False, "error": str(error)}