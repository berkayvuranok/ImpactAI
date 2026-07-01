"""Tests for webhook payload parsing."""

import hashlib
import hmac

from code_impact.application.services.webhook_service import (
    normalize_repo_url,
    parse_github_payload,
    parse_gitlab_payload,
    verify_github_signature,
)


def test_parse_github_pull_request():
    payload = {
        "action": "opened",
        "repository": {"html_url": "https://github.com/org/repo", "full_name": "org/repo"},
        "pull_request": {
            "number": 42,
            "title": "Fix parser",
            "body": "Details here",
            "head": {"sha": "abc"},
            "base": {"sha": "def"},
        },
    }
    event = parse_github_payload(payload)
    assert event is not None
    assert event.pr_number == 42
    assert event.diff.startswith("diff --git")


def test_parse_gitlab_merge_request():
    payload = {
        "object_kind": "merge_request",
        "object_attributes": {
            "action": "open",
            "iid": 7,
            "title": "Feature",
            "description": "MR body",
            "target_branch": "main",
            "last_commit": {"id": "sha123"},
        },
        "project": {"web_url": "https://gitlab.com/org/repo", "path_with_namespace": "org/repo"},
    }
    event = parse_gitlab_payload(payload)
    assert event is not None
    assert event.provider == "gitlab"


def test_github_signature_verification():
    secret = "test-secret"
    body = b'{"hello":"world"}'
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_github_signature(body, sig, secret)
    assert not verify_github_signature(body, "sha256=bad", secret)


def test_normalize_repo_url():
    assert normalize_repo_url("https://GitHub.com/Org/Repo.git/") == "https://github.com/org/repo"
