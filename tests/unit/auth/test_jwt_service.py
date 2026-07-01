"""Tests for JWT service."""

from uuid import uuid4

from code_impact.domain.value_objects.enums import UserRole
from code_impact.infrastructure.auth.jwt_service import JWTService
from code_impact.infrastructure.config.settings import Settings


def _settings() -> Settings:
    return Settings(
        secret_key="test-secret-key-minimum-32-chars-long",
        database_url="postgresql+asyncpg://cip:cip_secret@localhost:5432/code_impact_test",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="redis://localhost:6379/1",
        celery_result_backend="redis://localhost:6379/2",
    )


def test_create_and_decode_access_token():
    jwt = JWTService(_settings())
    user_id = uuid4()
    tokens = jwt.create_token_pair(user_id, "a@b.com", UserRole.VIEWER)
    payload = jwt.decode_token(tokens.access_token, expected_type="access")
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "a@b.com"
