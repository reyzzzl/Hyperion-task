class HyperionException(Exception):
    pass

class AgentException(HyperionException):
    pass

class RateLimitExceeded(AgentException):
    pass

class CircuitOpenError(AgentException):
    pass

class LLMTimeoutError(AgentException):
    pass

class WorkflowNotFoundError(HyperionException):
    pass