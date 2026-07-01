"""Tests for auth use cases."""

import pytest

from code_impact.application.use_cases.auth import LoginCommand, RegisterUserCommand, RegisterUserUseCase, LoginUseCase
from code_impact.domain.exceptions import AuthenticationError, ConflictError
from code_impact.infrastructure.auth.jwt_service import JWTService
from code_impact.infrastructure.config.settings import Settings
from support.in_memory_repositories import InMemoryUserRepository


def _settings() -> Settings:
    return Settings(
        secret_key="test-secret-key-minimum-32-chars-long",
        database_url="postgresql+asyncpg://cip:cip_secret@localhost:5432/code_impact_test",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="redis://localhost:6379/1",
        celery_result_backend="redis://localhost:6379/2",
    )


@pytest.mark.asyncio
async def test_register_and_login():
    users = InMemoryUserRepository()
    jwt = JWTService(_settings())
    register = RegisterUserUseCase(users, jwt)
    login = LoginUseCase(users, jwt)

    user, tokens = await register.execute(
        RegisterUserCommand(email="dev@example.com", username="dev", password="password123")
    )
    assert user.email == "dev@example.com"
    assert tokens.access_token

    user2, tokens2 = await login.execute(LoginCommand(email="dev@example.com", password="password123"))
    assert user2.id == user.id
    assert tokens2.refresh_token


@pytest.mark.asyncio
async def test_register_duplicate_email():
    users = InMemoryUserRepository()
    jwt = JWTService(_settings())
    register = RegisterUserUseCase(users, jwt)
    await register.execute(
        RegisterUserCommand(email="dup@example.com", username="one", password="password123")
    )
    with pytest.raises(ConflictError):
        await register.execute(
            RegisterUserCommand(email="dup@example.com", username="two", password="password123")
        )


@pytest.mark.asyncio
async def test_login_invalid_password():
    users = InMemoryUserRepository()
    jwt = JWTService(_settings())
    register = RegisterUserUseCase(users, jwt)
    login = LoginUseCase(users, jwt)
    await register.execute(
        RegisterUserCommand(email="x@example.com", username="x", password="password123")
    )
    with pytest.raises(AuthenticationError):
        await login.execute(LoginCommand(email="x@example.com", password="wrong"))
