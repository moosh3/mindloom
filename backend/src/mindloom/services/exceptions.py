# Custom exceptions for the services layer

class ServiceError(Exception):
    """Base class for service layer exceptions."""
    pass

class AgentCreationError(ServiceError):
    """Raised when an Agno agent instance cannot be created."""
    pass

class TeamCreationError(ServiceError):
    """Raised when an Agno team instance cannot be created."""
    pass

class KnowledgeCreationError(ServiceError):
    """Raised when configuring or updating knowledge fails."""
    pass

class StorageCreationError(ServiceError):
    """Raised when configuring storage fails."""
    pass
