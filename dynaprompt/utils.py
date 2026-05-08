"""Utility functions — object_merge and inspect_prompts."""

from __future__ import annotations

import json
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
    """Export the loaded prompt structure to a TOML file for user customization."""
    if prompts_instance._wrapped is None:
        prompts_instance._setup()

    raw_data = prompts_instance._wrapped._raw_data
    lines = [
        "# Auto-generated DynaPrompt structure",
        "# You can modify this file to override prompt templates and settings",
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
                if isinstance(v, dict):
                    # Simplistic inline table
                    items = ", ".join(
                        f'"{ik}" = {format_value(iv)}' for ik, iv in v.items()
                    )
                    lines.append(f"{k} = {{ {items} }}")
                else:
                    lines.append(f"{k} = {format_value(v)}")
            lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
