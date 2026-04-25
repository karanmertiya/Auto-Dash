from __future__ import annotations

import ast

DISALLOWED_NODES = (
    ast.AsyncFunctionDef,
    ast.Await,
    ast.ClassDef,
    ast.Delete,
    ast.For,
    ast.Global,
    ast.Import,
    ast.ImportFrom,
    ast.Lambda,
    ast.Nonlocal,
    ast.Raise,
    ast.Try,
    ast.While,
    ast.With,
)

DISALLOWED_NAMES = {
    "__import__",
    "breakpoint",
    "compile",
    "dir",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
}


class UnsafeScriptError(ValueError):
    pass


def validate_transform_script(script: str) -> ast.Module:
    tree = ast.parse(script)
    transform_defs = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "transform"
    ]
    if len(transform_defs) != 1:
        raise UnsafeScriptError("Script must define exactly one transform(df) function.")
    for node in ast.walk(tree):
        if isinstance(node, DISALLOWED_NODES):
            raise UnsafeScriptError(f"Disallowed Python syntax: {node.__class__.__name__}.")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise UnsafeScriptError("Dunder attribute access is not allowed.")
        if isinstance(node, ast.Name) and node.id in DISALLOWED_NAMES:
            raise UnsafeScriptError(f"Use of '{node.id}' is not allowed.")
        if isinstance(node, ast.Call):
            _validate_call(node)
    return tree


def _validate_call(node: ast.Call) -> None:
    if isinstance(node.func, ast.Name) and node.func.id in DISALLOWED_NAMES:
        raise UnsafeScriptError(f"Call to '{node.func.id}' is not allowed.")
    if isinstance(node.func, ast.Attribute):
        root = node.func
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(root, ast.Name) and root.id in {"os", "sys", "subprocess", "socket", "pathlib"}:
            raise UnsafeScriptError(f"Calls through '{root.id}' are not allowed.")

