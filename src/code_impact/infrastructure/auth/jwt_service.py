"""JWT token creation and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt

from code_impact.domain.value_objects.enums import UserRole
from code_impact.infrastructure.config.settings import Settings


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token


class JWTService:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_minutes = settings.access_token_expire_minutes
        self._refresh_days = settings.refresh_token_expire_days

    def create_token_pair(self, user_id: UUID, email: str, role: UserRole) -> TokenPair:
        access = self._create_token(user_id, email, role, "access", timedelta(minutes=self._access_minutes))
        refresh = self._create_token(user_id, email, role, "refresh", timedelta(days=self._refresh_days))
        return TokenPair(access, refresh)

    def create_access_token(self, user_id: UUID, email: str, role: UserRole) -> str:
        return self._create_token(
            user_id, email, role, "access", timedelta(minutes=self._access_minutes)
        )

    def decode_token(self, token: str, *, expected_type: str | None = None) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            msg = "Invalid or expired token"
            raise ValueError(msg) from exc
        if expected_type and payload.get("type") != expected_type:
            msg = f"Expected token type {expected_type}"
            raise ValueError(msg)
        return payload

    def _create_token(
        self,
        user_id: UUID,
        email: str,
        role: UserRole,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)
