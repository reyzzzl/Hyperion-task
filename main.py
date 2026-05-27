import asyncio
import logging
import os
import uvicorn
from hyperion_task.database.sqlite import TaskDatabase
from hyperion_task.integrations.notion_erp import NotionERPConnector
from hyperion_task.integrations.erp import DummyERPConnector
from hyperion_task.web.dashboard import app, set_workflow_manager
from hyperion_task.core.workflow_manager import WorkflowManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
    llm_backend = os.environ.get("LLM_BACKEND", "ollama").lower()
    if llm_backend not in ("ollama", "huggingface"):
        logger.warning(f"Unknown LLM_BACKEND '{llm_backend}', defaulting to ollama")
        llm_backend = "ollama"

    db = TaskDatabase()
    await db.connect()

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
            logger.info("GoogleWorkspace integration initialized.")
        except FileNotFoundError as e:
            logger.error(f"Google Workspace integration failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing Google Workspace: {e}")
    elif email_provider == "microsoft":
        tenant = os.environ.get("MS365_TENANT_ID", "")
        client_id = os.environ.get("MS365_CLIENT_ID", "")
        secret = os.environ.get("MS365_CLIENT_SECRET", "")
        if tenant and client_id and secret:
            try:
                from hyperion_task.integrations.microsoft365 import Microsoft365
                email_integration = Microsoft365(tenant, client_id, secret)
                logger.info("Microsoft365 integration initialized.")
            except ConnectionError as e:
                logger.error(f"Microsoft 365 authentication failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error initializing Microsoft 365: {e}")
        else:
            logger.warning("MS365 environment variables not set, email integration disabled.")
    else:
        logger.warning(f"Unknown or missing EMAIL_PROVIDER '{email_provider}'. Email integration disabled.")

    if email_integration:
        integrations["email"] = email_integration
    else:
        logger.warning("No email integration configured or initialized successfully.")

    workflow_manager = WorkflowManager(db, integrations)
    set_workflow_manager(workflow_manager)

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        log_level="info",
    )
    server = uvicorn.Server(config)

    try:
        await asyncio.gather(
            workflow_manager.start(),
            server.serve(),
        )
    finally:
        await workflow_manager.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")