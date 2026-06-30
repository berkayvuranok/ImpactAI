"""Bootstrap data for development."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from code_impact.domain.entities import User
from code_impact.domain.value_objects.enums import UserRole
from code_impact.infrastructure.persistence.models import UserModel
from code_impact.presentation.api.dependencies import SYSTEM_USER_ID

SYSTEM_USER_EMAIL = "system@code-impact.local"


async def ensure_system_user(session: AsyncSession) -> UUID:
    result = await session.execute(select(UserModel).where(UserModel.id == SYSTEM_USER_ID))
    if result.scalar_one_or_none():
        return SYSTEM_USER_ID

    user = User(
        id=SYSTEM_USER_ID,
        email=SYSTEM_USER_EMAIL,
        username="system",
        hashed_password="!",  # not used until auth is implemented
        role=UserRole.ADMIN,
    )
    session.add(
        UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )
    await session.commit()
    return SYSTEM_USER_ID
