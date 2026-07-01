"""VCS webhook endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status

from code_impact.application.schemas import WebhookAcceptedResponse
from code_impact.application.services.webhook_handler_service import WebhookHandlerService
from code_impact.application.services.webhook_service import (
    parse_github_payload,
    parse_gitlab_payload,
    verify_github_signature,
    verify_gitlab_token,
)
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.infrastructure.config.settings import Settings
from code_impact.presentation.api.dependencies import (
    SYSTEM_USER_ID,
    get_current_user,
    get_settings,
    get_webhook_handler,
)
from code_impact.domain.entities import User

router = APIRouter(prefix="/webhooks")


@router.post("/github", response_model=WebhookAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    handler: WebhookHandlerService = Depends(get_webhook_handler),
    current_user: User = Depends(get_current_user),
) -> WebhookAcceptedResponse:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(body, signature, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body)
    event = parse_github_payload(payload)
    if event is None:
        return WebhookAcceptedResponse(
            prediction_id=None,
            status="ignored",
            message="Event type not handled",
        )

    owner_id = current_user.id if settings.auth_enabled else SYSTEM_USER_ID
    try:
        prediction_id = await handler.handle(event, owner_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return WebhookAcceptedResponse(
        prediction_id=prediction_id,
        status="queued",
        message=f"GitHub PR #{event.pr_number} prediction queued",
    )


@router.post("/gitlab", response_model=WebhookAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def gitlab_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    handler: WebhookHandlerService = Depends(get_webhook_handler),
    current_user: User = Depends(get_current_user),
) -> WebhookAcceptedResponse:
    token = request.headers.get("X-Gitlab-Token")
    if not verify_gitlab_token(token, settings.gitlab_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    payload = await request.json()
    event = parse_gitlab_payload(payload)
    if event is None:
        return WebhookAcceptedResponse(
            prediction_id=None,
            status="ignored",
            message="Event type not handled",
        )

    owner_id = current_user.id if settings.auth_enabled else SYSTEM_USER_ID
    try:
        prediction_id = await handler.handle(event, owner_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return WebhookAcceptedResponse(
        prediction_id=prediction_id,
        status="queued",
        message=f"GitLab MR !{event.pr_number} prediction queued",
    )
