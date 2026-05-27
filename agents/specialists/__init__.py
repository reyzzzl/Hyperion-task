from .marketing import MarketingAgent
from .sales import SalesAgent
from .support import SupportAgent
from .operations import OperationsAgent
from .hr import HRAgent
from .finance import FinanceAgent
from .it import ITAgent
from .legal import LegalAgent
from .executive import ExecutiveAgent

from ..registry import AgentRegistry

def register_all_agents():
    AgentRegistry.register("marketing", MarketingAgent)
    AgentRegistry.register("sales", SalesAgent)
    AgentRegistry.register("support", SupportAgent)
    AgentRegistry.register("operations", OperationsAgent)
    AgentRegistry.register("hr", HRAgent)
    AgentRegistry.register("finance", FinanceAgent)
    AgentRegistry.register("it", ITAgent)
    AgentRegistry.register("legal", LegalAgent)
    AgentRegistry.register("executive", ExecutiveAgent)

register_all_agents()