"""Domain-specific exceptions."""

from uuid import UUID


class DomainError(Exception):
    """Base domain exception."""


class EntityNotFoundError(DomainError):
    def __init__(self, entity_type: str, entity_id: UUID | str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id}")


class ValidationError(DomainError):
    pass


class AuthorizationError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class RepositorySyncError(DomainError):
    pass


class PredictionPipelineError(DomainError):
    pass


class ModelNotAvailableError(DomainError):
    pass
