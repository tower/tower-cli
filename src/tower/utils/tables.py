from typing import Optional


def make_table_name(name: str, namespace: Optional[str]) -> str:
    namespace = namespace_or_default(namespace)

    if "." in name:
        return name
    else:
        return f"{namespace}.{name}"


def namespace_of(table_name: str) -> str:
    """Return the namespace part of a qualified table name ("sales.orders" -> "sales")."""
    return table_name.rsplit(".", 1)[0]


def namespace_or_default(namespace: Optional[str]) -> str:
    if namespace is None:
        return "default"
    else:
        return namespace
