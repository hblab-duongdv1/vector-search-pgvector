"""Domain-level exceptions (mapped to HTTP in the interface layer)."""


class DomainError(Exception):
    """Base class for domain errors."""


class NotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} not found: {identifier}")


class ConflictError(DomainError):
    """Raised when a create/update violates a uniqueness constraint."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
