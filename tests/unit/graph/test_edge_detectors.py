"""Unit tests for edge detectors."""

from code_impact.infrastructure.graph.edge_detectors import (
    detect_api_targets,
    detect_db_targets,
    detect_mq_targets,
)


def test_detect_api_targets():
    source = "import httpx\nhttpx.get('https://example.com')"
    assert "httpx" in detect_api_targets(source)


def test_detect_db_targets():
    source = "session.query(User).all()\nsession.commit()"
    assert "sqlalchemy" in detect_db_targets(source)


def test_detect_mq_targets():
    source = "@celery_app.task\ndef process(): pass\nprocess.delay()"
    assert "celery" in detect_mq_targets(source)
