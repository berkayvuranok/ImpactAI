"""Detect API, database, and message-queue dependencies from source text."""

from __future__ import annotations

import re

API_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("httpx", re.compile(r"\bhttpx\.(get|post|put|patch|delete|request)\b")),
    ("requests", re.compile(r"\brequests\.(get|post|put|patch|delete|request)\b")),
    ("fetch", re.compile(r"\bfetch\s*\(")),
    ("axios", re.compile(r"\baxios\.(get|post|put|patch|delete|request)\b")),
    ("urllib", re.compile(r"\burllib\.request\b")),
    ("aiohttp", re.compile(r"\baiohttp\.(ClientSession|request)\b")),
]

DB_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("sqlalchemy", re.compile(r"\bsession\.(query|execute|commit|add)\b|\bSQLAlchemy\b")),
    ("asyncpg", re.compile(r"\basyncpg\.(connect|create_pool)\b")),
    ("psycopg", re.compile(r"\bpsycopg2?\.(connect|cursor)\b")),
    ("pymongo", re.compile(r"\bpymongo\.(MongoClient|collection)\b")),
    ("redis_db", re.compile(r"\.(?:get|set|hget|hset|lpush|rpush)\s*\(")),
    ("prisma", re.compile(r"\bprisma\.\w+\.(find|create|update|delete)")),
    ("mongoose", re.compile(r"\bmongoose\.(connect|model)\b")),
]

MQ_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("celery", re.compile(r"\b(?:\.delay|\.apply_async|@(?:shared_task|task|celery_app\.task))\b")),
    ("kafka", re.compile(r"\bKafkaProducer\b|\bKafkaConsumer\b")),
    ("rabbitmq", re.compile(r"\bpika\.(?:BlockingConnection|URLParameters)\b")),
    ("redis_pubsub", re.compile(r"\.publish\s*\(|\.subscribe\s*\(")),
    ("sqs", re.compile(r"\bboto3\.(?:client|resource)\(\s*['\"]sqs['\"]")),
]


def detect_api_targets(source: str) -> list[str]:
    return _match_patterns(source, API_PATTERNS)


def detect_db_targets(source: str) -> list[str]:
    return _match_patterns(source, DB_PATTERNS)


def detect_mq_targets(source: str) -> list[str]:
    return _match_patterns(source, MQ_PATTERNS)


def _match_patterns(source: str, patterns: list[tuple[str, re.Pattern[str]]]) -> list[str]:
    found: list[str] = []
    for name, pattern in patterns:
        if pattern.search(source):
            found.append(name)
    return found
