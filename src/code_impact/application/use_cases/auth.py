"""Authentication and authorization use cases."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from code_impact.domain.entities import User
from code_impact.domain.exceptions import AuthenticationError, AuthorizationError, ConflictError
from code_impact.domain.repositories import IUserRepository
from code_impact.domain.value_objects.enums import UserRole
from code_impact.infrastructure.auth.jwt_service import JWTService, TokenPair
from code_impact.infrastructure.auth.password_service import hash_password, verify_password


@dataclass
class RegisterUserCommand:
    email: str
    username: str
    password: str


@dataclass
class LoginCommand:
    email: str
    password: str


@dataclass
class RefreshTokenCommand:
    refresh_token: str


class RegisterUserUseCase:
    def __init__(self, user_repo: IUserRepository, jwt_service: JWTService) -> None:
        self._users = user_repo
        self._jwt = jwt_service

    async def execute(self, command: RegisterUserCommand) -> tuple[User, TokenPair]:
        existing = await self._users.get_by_email(command.email.lower())
        if existing:
            raise ConflictError("Email already registered")

        user = User(
            id=uuid4(),
            email=command.email.lower(),
            username=command.username,
            hashed_password=hash_password(command.password),
            role=UserRole.VIEWER,
        )
        user = await self._users.create(user)
        tokens = self._jwt.create_token_pair(user.id, user.email, user.role)
        return user, tokens


class LoginUseCase:
    def __init__(self, user_repo: IUserRepository, jwt_service: JWTService) -> None:
        self._users = user_repo
        self._jwt = jwt_service

    async def execute(self, command: LoginCommand) -> tuple[User, TokenPair]:
        user = await self._users.get_by_email(command.email.lower())
        if not user or not verify_password(command.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthorizationError("Account is disabled")
        tokens = self._jwt.create_token_pair(user.id, user.email, user.role)
        return user, tokens


class RefreshTokenUseCase:
    def __init__(self, user_repo: IUserRepository, jwt_service: JWTService) -> None:
        self._users = user_repo
        self._jwt = jwt_service

    async def execute(self, command: RefreshTokenCommand) -> TokenPair:
        try:
            payload = self._jwt.decode_token(command.refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise AuthenticationError(str(exc)) from exc

        from uuid import UUID

        user = await self._users.get_by_id(UUID(payload["sub"]))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        return self._jwt.create_token_pair(user.id, user.email, user.role)
