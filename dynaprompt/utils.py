"""Utility functions — object_merge, inspect_prompts, resolve_path_spec."""

from __future__ import annotations

import json
import pathlib
import sys


def object_merge(base: dict, override: dict) -> None:
    """
    Deep-merge `override` into `base` in-place.
    Dicts are merged recursively; all other types replace.
    Inspired by Dynaconf's object_merge utility.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            object_merge(base[key], value)
        else:
            base[key] = value


def sanitize_name(stem: str) -> str:
    """Normalize a filename stem to a valid, snake_case prompt identifier.

    Examples::

        "Customer Support"  -> "customer_support"
        "call-analysis"     -> "call_analysis"
        "01_intro"          -> "p_01_intro"
        ""                  -> "prompt"
    """
    import re

    name = stem.lower()
    # Replace any run of non-alphanumeric chars with a single underscore
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    if not name:
        return "prompt"
    # Identifiers must not start with a digit
    if name[0].isdigit():
        name = f"p_{name}"
    return name


_PATH_EXTENSIONS = (".py", ".toml", ".json", ".yaml", ".yml", ".md", ".txt")


def resolve_path_spec(
    spec: str,
    base_dir: pathlib.Path | None = None,
    extensions: tuple[str, ...] = _PATH_EXTENSIONS,
) -> tuple[pathlib.Path | None, str | None]:
    """
    Resolve a flexible path/module specification to ``(file_path, attr_name)``.

    Supported formats
    -----------------
    File-based (contains ``/`` or ``\\``):

        ``"prompts/cs.md"``           →  (Path, None)
        ``"config/var.py:variables"`` →  (Path, "variables")
        ``"config/var"``              →  (Path, None)   ← auto-detect extension

    Dotted module-style (no slashes):

        ``"config.var"``              →  (Path("config/var.py"), None)
        ``"config.var:variables"``    →  (Path("config/var.py"), "variables")
        ``"config.var.variables"``    →  (Path("config/var.py"), "variables")

    Returns ``(resolved_path, attr_name)`` or ``(None, None)`` if unresolvable.
    """
    base = pathlib.Path(base_dir) if base_dir else pathlib.Path.cwd()
    attr: str | None = None

    # 1. Split explicit attribute via ":"
    if ":" in spec:
        path_part, attr_raw = spec.split(":", 1)
        attr = attr_raw.strip() or None
    else:
        path_part = spec

    is_file_path = "/" in path_part or "\\" in path_part

    def _try_resolve(candidate: pathlib.Path) -> pathlib.Path | None:
        """Try candidate path, then candidate + known extensions."""
        resolved = (base / candidate).resolve()
        if resolved.exists() and resolved.is_file():
            return resolved
        for ext in extensions:
            with_ext = resolved.with_suffix(ext)
            if with_ext.exists():
                return with_ext
        return None

    # 2a. File-based path
    if is_file_path:
        found = _try_resolve(pathlib.Path(path_part))
        return (found, attr) if found else (None, None)

    # 2b. Dotted module-style path
    parts = path_part.split(".")

    if attr is not None:
        # All parts → module path, attr already known
        found = _try_resolve(pathlib.Path(*parts))
        return (found, attr) if found else (None, None)

    # No explicit attr — try splitting last part(s) off as attribute
    for split_at in range(len(parts), 0, -1):
        module_parts = parts[:split_at]
        remaining = parts[split_at:]
        found = _try_resolve(pathlib.Path(*module_parts))
        if found:
            return found, ".".join(remaining) if remaining else None

    return None, None


def inspect_prompts(
    prompts,
    key: str | None = None,
    print_report: bool = True,
    to_file: str | None = None,
) -> dict:
    """
    Print or return the loading history of a DynaPrompt instance.
    Mirrors Dynaconf's inspect_settings().

    Args:
        prompts:      A DynaPrompt instance.
        key:          If provided, show history only for that prompt name.
        print_report: If True, print to stdout.
        to_file:      If provided, write JSON report to this file path.

    Returns:
        dict with 'current' and 'history' keys.
    """
    history = prompts.inspect(key)
    current = None

    if key:
        try:
            node = prompts.get(key)
            current = {"template": node.text, **node.metadata}
        except AttributeError:
            current = None
    else:
        current = {}
        if prompts._wrapped:
            for name, data in prompts._wrapped._store.items():
                current[name] = data

    report = {
        "header": {
            "env": prompts.current_env,
            "key_filter": str(key),
        },
        "current": current,
        "history": history,
    }

    if print_report:
        json.dump(report, sys.stdout, indent=2, default=str)
        print()

    if to_file:
        with open(to_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    return report


def export_to_toml(prompts_instance, filepath: str = "pyprompts.toml") -> None:
    """Export the loaded prompt structure to a TOML file for user customization.

    Multiline templates are saved as individual files under a ``prompts/``
    directory beside the TOML file, and referenced by relative path.  This
    keeps the TOML compact and easy to diff.
    """
    import os

    if prompts_instance._wrapped is None:
        prompts_instance._setup()

    raw_data = prompts_instance._wrapped._raw_data
    toml_dir = pathlib.Path(filepath).parent.resolve()
    prompts_dir = toml_dir / "prompts"

    lines = [
        "# Auto-generated DynaPrompt structure",
        "# You can modify this file to override prompt templates and settings",
        "# Templates are stored in the prompts/ directory and referenced by path",
        "",
    ]

    def format_value(v):
        if isinstance(v, str):
            v = v.replace("\\", "\\\\").replace('"', '\\"')
            if "\n" in v:
                return f'"""\n{v}\n"""'
            return f'"{v}"'
        elif isinstance(v, bool):
            return str(v).lower()
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, list):
            items = ", ".join(format_value(i) for i in v)
            return f"[{items}]"
        elif v is None:
            return '""'
        else:
            v_str = str(v).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{v_str}"'

    for env, prompts in raw_data.items():
        for name, data in prompts.items():
            section_name = f"{env}.{name}"
            lines.append(f"[{section_name}]")
            for k, v in data.items():
                if k.startswith("_"):
                    continue

                if k == "template" and isinstance(v, str):
                    # Read file content if it's a file path
                    if os.path.isfile(v):
                        try:
                            with open(v, encoding="utf-8") as f:
                                v = f.read()
                        except Exception:
                            pass

                    # Save multiline templates to files, reference by path
                    if "\n" in v and len(v) > 80:
                        prompt_file = prompts_dir / f"{name}.md"
                        prompts_dir.mkdir(parents=True, exist_ok=True)
                        prompt_file.write_text(v.strip() + "\n", encoding="utf-8")
                        rel_path = prompt_file.relative_to(toml_dir).as_posix()
                        lines.append(f'{k} = "{rel_path}"')
                        continue

                if isinstance(v, dict):
                    items = ", ".join(
                        f'"{ik}" = {format_value(iv)}' for ik, iv in v.items()
                    )
                    lines.append(f"{k} = {{ {items} }}")
                else:
                    lines.append(f"{k} = {format_value(v)}")
            lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
