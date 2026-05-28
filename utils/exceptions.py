class HyperionException(Exception):
    pass

class ConfigurationError(HyperionException):
    pass

class WorkflowError(HyperionException):
    pass

class WorkflowNotFoundError(WorkflowError):
    pass

class WorkflowExecutionError(WorkflowError):
    pass

class NodeExecutionError(WorkflowError):
    pass

class TemplateError(HyperionException):
    pass

class TemplateRenderError(TemplateError):
    pass

class TemplateParseError(TemplateError):
    pass

class AgentException(HyperionException):
    pass

class AgentNotFoundError(AgentException):
    pass

class AgentTimeoutError(AgentException):
    pass

class RateLimitExceeded(AgentException):
    pass

class CircuitOpenError(AgentException):
    pass

class LLMTimeoutError(AgentException):
    pass

class LLMError(AgentException):
    pass

class IntegrationError(HyperionException):
    pass

class GoogleWorkspaceError(IntegrationError):
    pass

class Microsoft365Error(IntegrationError):
    pass

class NotionError(IntegrationError):
    pass

class DatabaseError(HyperionException):
    pass

class DatabaseConnectionError(DatabaseError):
    pass

class DatabaseQueryError(DatabaseError):
    pass

class AuthenticationError(HyperionException):
    pass

class InvalidTokenError(AuthenticationError):
    pass

class PermissionDeniedError(AuthenticationError):
    pass

class ValidationError(HyperionException):
    pass

class ResourceNotFoundError(HyperionException):
    pass

class ConflictError(HyperionException):
    pass

class RateLimitError(HyperionException):
    pass

class ShutdownError(HyperionException):
    pass