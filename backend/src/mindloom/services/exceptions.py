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

class AgentRunError(ServiceError):
    """Raised when an agent run fails."""
    pass

class ToolCreationError(ServiceError):
    """Raised when a tool instance cannot be created."""
    pass
    
class ModelCreationError(ServiceError):
    """Raised when a model instance cannot be created."""
    pass
    
class ConfigurationError(ServiceError):
    """Raised when a configuration is invalid."""
    pass

class EmbedderCreationError(ServiceError):
    """Raised when an embedder instance cannot be created."""
    pass

class VectorStoreCreationError(ServiceError):
    """Raised when a vector store instance cannot be created."""
    pass

class StorageCreationError(ServiceError):
    """Raised when a storage instance cannot be created."""
    pass
    