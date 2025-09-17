from typing import Optional


def make_table_name(name: str, namespace: Optional[str]) -> str:
    namespace = namespace_or_default(namespace)

    if "." in name:
        return name
    else:
        return f"{namespace}.{name}"


def namespace_or_default(namespace: Optional[str]) -> str:
    if namespace is None:
        return "default"
    else:
        return namespace
