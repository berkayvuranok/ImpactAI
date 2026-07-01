"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from code_impact.application.schemas import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from code_impact.application.use_cases.auth import (
    LoginCommand,
    LoginUseCase,
    RefreshTokenCommand,
    RefreshTokenUseCase,
    RegisterUserCommand,
    RegisterUserUseCase,
)
from code_impact.domain.exceptions import AuthenticationError, AuthorizationError, ConflictError
from code_impact.infrastructure.auth.rate_limiter import RateLimitExceeded, RateLimiter
from code_impact.presentation.api.dependencies import (
    get_login_use_case,
    get_rate_limiter,
    get_refresh_token_use_case,
    get_register_user_use_case,
)

router = APIRouter(prefix="/auth")


def _auth_response(user, tokens) -> AuthResponse:
    return AuthResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.value,
        ),
    )


async def _rate_limit(request: Request, limiter: RateLimiter) -> None:
    client = request.client.host if request.client else "unknown"
    try:
        await limiter.check(f"auth:{client}")
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> AuthResponse:
    await _rate_limit(request, limiter)
    try:
        user, tokens = await use_case.execute(
            RegisterUserCommand(email=body.email, username=body.username, password=body.password)
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _auth_response(user, tokens)


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    request: Request,
    use_case: LoginUseCase = Depends(get_login_use_case),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> AuthResponse:
    await _rate_limit(request, limiter)
    try:
        user, tokens = await use_case.execute(LoginCommand(email=body.email, password=body.password))
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _auth_response(user, tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
) -> TokenResponse:
    try:
        tokens = await use_case.execute(RefreshTokenCommand(refresh_token=body.refresh_token))
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)
