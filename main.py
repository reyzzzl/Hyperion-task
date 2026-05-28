import asyncio
import logging
import os
import uvicorn
from hyperion_task.core.database import AsyncSessionLocal, init_db_with_retry
from hyperion_task.database import WorkflowDatabase
from hyperion_task.web.dashboard import app, set_workflow_manager, set_agent_orchestrator
from hyperion_task.core.workflow_manager import WorkflowManager
from hyperion_task.agents import AgentOrchestrator
from hyperion_task.integrations.notion_erp import NotionERPConnector
from hyperion_task.integrations.erp import DummyERPConnector
from hyperion_task.utils.logging import setup_logging

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"), json_format=True)
logger = logging.getLogger("Main")

def get_erp_connector():
    notion_token = os.environ.get("NOTION_API_TOKEN")
    if not notion_token:
        return None
    databases = {
        "orders": os.environ.get("NOTION_DB_ORDERS", ""),
        "tickets": os.environ.get("NOTION_DB_TICKETS", ""),
        "transactions": os.environ.get("NOTION_DB_TRANSACTIONS", ""),
        "inventory": os.environ.get("NOTION_DB_INVENTORY", ""),
    }
    return NotionERPConnector(notion_token, databases)

async def main():
    await init_db_with_retry(max_retries=5, delay=2.0)

    worker_session = AsyncSessionLocal()
    try:
        db = WorkflowDatabase(worker_session, org_id=None)

        erp = get_erp_connector()
        if not erp:
            logger.info("No ERP configured, using DummyERPConnector")
            erp = DummyERPConnector()

        integrations = {"erp": erp}
        email_provider = os.environ.get("EMAIL_PROVIDER", "").lower()
        email_integration = None
        if email_provider == "google":
            try:
                from hyperion_task.integrations.google_workspace import GoogleWorkspace
                email_integration = GoogleWorkspace()
                logger.info("Google Workspace integration initialized")
            except Exception as e:
                logger.error(f"Google Workspace integration failed: {e}")
        elif email_provider == "microsoft":
            tenant = os.environ.get("MS365_TENANT_ID", "")
            client_id = os.environ.get("MS365_CLIENT_ID", "")
            secret = os.environ.get("MS365_CLIENT_SECRET", "")
            if tenant and client_id and secret:
                try:
                    from hyperion_task.integrations.microsoft365 import Microsoft365
                    email_integration = Microsoft365(tenant, client_id, secret)
                    logger.info("Microsoft 365 integration initialized")
                except Exception as e:
                    logger.error(f"Microsoft 365 integration failed: {e}")
        if email_integration:
            integrations["email"] = email_integration

        workflow_manager = WorkflowManager(db, integrations)
        set_workflow_manager(workflow_manager)

        agent_orchestrator = AgentOrchestrator(integrations, workflow_executor=workflow_manager.executor)
        set_agent_orchestrator(agent_orchestrator)

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 8000)),
            log_level="info",
        )
        server = uvicorn.Server(config)

        tasks = [
            asyncio.create_task(workflow_manager.start()),
            asyncio.create_task(server.serve()),
        ]
        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        finally:
            try:
                await workflow_manager.close()
            except Exception as e:
                logger.error(f"Error closing workflow manager: {e}")
            try:
                await agent_orchestrator.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down agent orchestrator: {e}")
            if email_integration and hasattr(email_integration, 'close'):
                try:
                    await email_integration.close()
                except Exception as e:
                    logger.error(f"Error closing email integration: {e}")
            if isinstance(erp, NotionERPConnector) and hasattr(erp, 'close'):
                try:
                    await erp.close()
                except Exception as e:
                    logger.error(f"Error closing ERP connector: {e}")
    finally:
        await worker_session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")