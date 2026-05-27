from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ERPConnector(ABC):
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict:
        pass

    @abstractmethod
    async def update_crm_lead(self, lead_id: str, status: str) -> Dict:
        pass

    @abstractmethod
    async def create_support_ticket(self, customer_email: str, issue: str) -> Dict:
        pass

    @abstractmethod
    async def record_transaction(self, amount: float, description: str) -> Dict:
        pass

    @abstractmethod
    async def manage_inventory(self, item_id: str, quantity_change: int) -> Dict:
        pass


class DummyERPConnector(ERPConnector):
    async def get_order_status(self, order_id: str) -> Dict:
        return {"order_id": order_id, "status": "processing", "estimated_delivery": "2026-06-01"}

    async def update_crm_lead(self, lead_id: str, status: str) -> Dict:
        return {"success": True}

    async def create_support_ticket(self, customer_email: str, issue: str) -> Dict:
        return {"ticket_id": "dummy_ticket", "status": "open"}

    async def record_transaction(self, amount: float, description: str) -> Dict:
        return {"success": True}

    async def manage_inventory(self, item_id: str, quantity_change: int) -> Dict:
        return {"new_quantity": "unknown"}