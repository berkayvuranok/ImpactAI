"""Unit tests for import resolver."""

from code_impact.infrastructure.graph.import_resolver import parse_import_modules, resolve_module_to_file


def test_parse_import_modules_from():
    assert parse_import_modules("from app.service import UserService") == ["app.service"]


def test_parse_import_modules_import():
    assert "os" in parse_import_modules("import os, sys")


def test_resolve_module_to_file():
    files = {"app/service.py", "utils.py"}
    assert resolve_module_to_file("app.service", files) == "app/service.py"
