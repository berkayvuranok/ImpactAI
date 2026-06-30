"""Canonical node ID generation for dependency graphs."""

from code_impact.domain.value_objects.enums import NodeType


def make_node_id(node_type: NodeType, *parts: str) -> str:
    prefix = node_type.value
    return f"{prefix}:{'::'.join(parts)}"


def file_id(file_path: str) -> str:
    return make_node_id(NodeType.FILE, file_path)


def class_id(file_path: str, class_name: str) -> str:
    return make_node_id(NodeType.CLASS, file_path, class_name)


def function_id(file_path: str, qualified_name: str) -> str:
    return make_node_id(NodeType.FUNCTION, file_path, qualified_name)


def module_id(module_name: str) -> str:
    return make_node_id(NodeType.MODULE, module_name)


def service_id(service_name: str) -> str:
    return make_node_id(NodeType.SERVICE, service_name)
