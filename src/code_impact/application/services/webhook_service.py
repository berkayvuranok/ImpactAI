"""Parse and verify VCS webhook payloads."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WebhookEvent:
    provider: str
    event_type: str
    repository_url: str
    repository_name: str
    diff: str
    base_sha: str | None
    head_sha: str | None
    pr_number: int | None
    pr_title: str


def verify_github_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def verify_gitlab_token(header_token: str | None, secret: str) -> bool:
    if not secret:
        return True
    return header_token == secret


def parse_github_payload(payload: dict) -> WebhookEvent | None:
    action = payload.get("action", "")
    if payload.get("pull_request") and action not in {"opened", "synchronize", "reopened"}:
        return None

    pr = payload.get("pull_request") or {}
    repo = payload.get("repository") or {}
    if not repo:
        return None

    pr_number = pr.get("number")
    title = pr.get("title", "")
    head = pr.get("head") or {}
    base = pr.get("base") or {}
    diff = _synthetic_diff(repo.get("full_name", "unknown"), pr_number, title, pr.get("body", ""))

    return WebhookEvent(
        provider="github",
        event_type=payload.get("action") or "pull_request",
        repository_url=repo.get("html_url", ""),
        repository_name=repo.get("full_name", repo.get("name", "")),
        diff=diff,
        base_sha=base.get("sha"),
        head_sha=head.get("sha"),
        pr_number=pr_number,
        pr_title=title,
    )


def parse_gitlab_payload(payload: dict) -> WebhookEvent | None:
    attrs = payload.get("object_attributes") or {}
    if payload.get("object_kind") != "merge_request":
        return None
    if attrs.get("action") not in {"open", "update", "reopen"}:
        return None

    project = payload.get("project") or {}
    web_url = project.get("web_url", "")
    pr_number = attrs.get("iid") or attrs.get("id")
    title = attrs.get("title", "")

    diff = _synthetic_diff(project.get("path_with_namespace", "unknown"), pr_number, title, attrs.get("description", ""))
    return WebhookEvent(
        provider="gitlab",
        event_type=attrs.get("action", "merge_request"),
        repository_url=web_url,
        repository_name=project.get("path_with_namespace", ""),
        diff=diff,
        base_sha=attrs.get("target_branch"),
        head_sha=attrs.get("last_commit", {}).get("id") if isinstance(attrs.get("last_commit"), dict) else None,
        pr_number=int(pr_number) if pr_number else None,
        pr_title=title,
    )


def _synthetic_diff(repo_name: str, pr_number: int | None, title: str, body: str) -> str:
    path = f"webhook/{repo_name.replace('/', '_')}/pr-{pr_number or 0}.md"
    content = (body or title or "Webhook triggered change")[:2000]
    lines = content.splitlines() or ["webhook placeholder"]
    diff_lines = [
        f"diff --git a/{path} b/{path}",
        f"--- a/{path}",
        f"+++ b/{path}",
        "@@ -0,0 +1,%d @@" % len(lines),
    ]
    diff_lines.extend(f"+{line}" for line in lines)
    return "\n".join(diff_lines) + "\n"


def normalize_repo_url(url: str) -> str:
    u = url.rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    return u.lower()
