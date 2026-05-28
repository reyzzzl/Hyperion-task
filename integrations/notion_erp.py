import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx
from .erp import ERPConnector

logger = logging.getLogger("NotionERP")


class NotionERPConnector(ERPConnector):
    def __init__(self, api_token: str, databases: Dict[str, str]):
        self.api_token = api_token
        self.databases = databases
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.client = httpx.AsyncClient(headers=self.headers)

    async def close(self):
        await self.client.aclose()

    async def _notion_request(self, method: str, endpoint: str, json_data: Optional[Dict] = None, retries: int = 3) -> Dict:
        url = f"{self.base_url}{endpoint}"
        for attempt in range(retries):
            try:
                if method.upper() == "GET":
                    resp = await self.client.get(url, params=json_data)
                elif method.upper() == "POST":
                    resp = await self.client.post(url, json=json_data)
                elif method.upper() == "PATCH":
                    resp = await self.client.patch(url, json=json_data)
                else:
                    return {"error": f"Unsupported method {method}"}
                
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 1))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                if resp.status_code not in (200, 201, 204):
                    logger.error(f"Notion API error: {resp.status_code} - {resp.text}")
                    return {"error": resp.text}
                    
                return resp.json() if resp.text else {"success": True}
            except httpx.RequestError as e:
                logger.error(f"Network error (attempt {attempt+1}): {e}")
                await asyncio.sleep(2 ** attempt)
        return {"error": "Max retries exceeded"}

    async def get_order_status(self, order_id: str) -> Dict:
        if "orders" not in self.databases:
            return {"error": "Orders database not configured"}
        query = {
            "filter": {
                "property": "Order ID",
                "rich_text": {"equals": order_id}
            }
        }
        result = await self._notion_request("POST", f"/databases/{self.databases['orders']}/query", json_data=query)
        if "results" in result and len(result["results"]) > 0:
            page = result["results"][0]
            status_prop = page.get("properties", {}).get("Status", {})
            status = "unknown"
            if status_prop.get("type") == "status":
                status = status_prop["status"]["name"]
            elif status_prop.get("type") == "select":
                status = status_prop["select"]["name"] if status_prop["select"] else "unknown"
            return {"order_id": order_id, "status": status, "source": "notion"}
        return {"order_id": order_id, "status": "not_found", "source": "notion"}

    async def get_inventory(self, item_id: str) -> Dict:
        if "inventory" not in self.databases:
            return {"error": "Inventory database not configured"}
        query = {
            "filter": {
                "property": "Item ID",
                "rich_text": {"equals": item_id}
            }
        }
        result = await self._notion_request("POST", f"/databases/{self.databases['inventory']}/query", json_data=query)
        if "results" in result and len(result["results"]) > 0:
            page = result["results"][0]
            quantity = page.get("properties", {}).get("Quantity", {}).get("number", 0)
            return {"item_id": item_id, "quantity": quantity, "source": "notion"}
        return {"item_id": item_id, "quantity": 0, "source": "notion", "error": "Item not found"}

    async def update_crm_lead(self, lead_id: str, status: str) -> Dict:
        if "orders" not in self.databases:
            return {"error": "Orders database not configured"}
        payload = {
            "properties": {
                "Status": {"status": {"name": status}}
            }
        }
        await self._notion_request("PATCH", f"/pages/{lead_id}", json_data=payload)
        return {"success": True, "lead_id": lead_id, "status": status}

    async def create_support_ticket(self, customer_email: str, issue: str) -> Dict:
        if "tickets" not in self.databases:
            return {"error": "Tickets database not configured"}
        payload = {
            "parent": {"database_id": self.databases["tickets"]},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"Support: {customer_email}"}}]
                },
                "Email": {"email": customer_email},
                "Issue": {"rich_text": [{"text": {"content": issue}}]},
                "Status": {"status": {"name": "Open"}}
            }
        }
        result = await self._notion_request("POST", "/pages", json_data=payload)
        return {
            "ticket_id": result.get("id", "unknown"),
            "status": "open",
            "url": result.get("url", ""),
        }

    async def record_transaction(self, amount: float, description: str) -> Dict:
        if "transactions" not in self.databases:
            return {"error": "Transactions database not configured"}
        payload = {
            "parent": {"database_id": self.databases["transactions"]},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": description}}]
                },
                "Amount": {"number": amount},
                "Type": {"select": {"name": "Transaction"}}
            }
        }
        result = await self._notion_request("POST", "/pages", json_data=payload)
        return {"success": True, "transaction_id": result.get("id")}

    async def manage_inventory(self, item_id: str, quantity_change: int) -> Dict:
        if "inventory" not in self.databases:
            return {"error": "Inventory database not configured"}
        query = {
            "filter": {
                "property": "Item ID",
                "rich_text": {"equals": item_id}
            }
        }
        result = await self._notion_request("POST", f"/databases/{self.databases['inventory']}/query", json_data=query)
        if "results" in result and len(result["results"]) > 0:
            page = result["results"][0]
            current_qty = page.get("properties", {}).get("Quantity", {}).get("number", 0)
            new_qty = current_qty + quantity_change
            payload = {"properties": {"Quantity": {"number": new_qty}}}
            await self._notion_request("PATCH", f"/pages/{page['id']}", json_data=payload)
            return {"item_id": item_id, "new_quantity": new_qty}
        return {"error": "Item not found"}