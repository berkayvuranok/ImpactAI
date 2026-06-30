"""Domain enumerations."""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SERVICE_ACCOUNT = "service_account"


class RepositoryProvider(StrEnum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LOCAL = "local"


class PredictionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeType(StrEnum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    MODULE = "module"
    SERVICE = "service"


class EdgeType(StrEnum):
    IMPORT = "import"
    CALL = "call"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    API_CALL = "api_call"
    DATABASE_ACCESS = "database_access"
    MESSAGE_QUEUE = "message_queue"
    MICROSERVICE = "microservice"


class IssueType(StrEnum):
    BUG = "bug"
    REGRESSION = "regression"
    FEATURE = "feature"
    TECH_DEBT = "tech_debt"


class SyncJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EmbeddingEntityType(StrEnum):
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    FILE = "file"
    DOCUMENT = "document"
