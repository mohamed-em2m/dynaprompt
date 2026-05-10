"""
TOML loader — primary configuration format.

Expected file structure::

    [default.customer_support]
    version = "1.0"
    template = "You are a helpful assistant. Customer: {{ user_name }}"
    model = "gpt-4.1"
    temperature = 0.3

    [production.customer_support]
    model = "gpt-4.1"          # override only what changes

    [development.customer_support]
    model = "gpt-4.1-mini"
    temperature = 0.7
"""

from __future__ import annotations

import pathlib
from typing import Any

from .base import PromptLoader

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # pip install tomli for < 3.11
    except ImportError:
        tomllib = None


class TomlLoader(PromptLoader):
    def can_handle(self, path: pathlib.Path) -> bool:
        return path.suffix in (".toml",)

    def load(self, path: pathlib.Path) -> dict[str, dict[str, Any]]:
        if tomllib is None:
            raise ImportError(
                "TOML support requires Python 3.11+ or `pip install tomli`"
            )

        with open(path, "rb") as f:
            raw = tomllib.load(f)

        result: dict[str, dict[str, Any]] = {}
        for env_key, env_data in raw.items():
            if not isinstance(env_data, dict):
                continue
            result[env_key] = {}
            # Flatten the nested dictionary from TOML to restore dotted names
            flat_prompts = self._flatten_toml(env_data)

            for prompt_name, data in flat_prompts.items():
                if isinstance(data, dict):
                    data = self._resolve_paths(data, path.parent)
                    result[env_key][prompt_name] = data

        return result

    # ------------------------------------------------------------------
    # Path resolution helpers
    # ------------------------------------------------------------------

    def _flatten_toml(self, d: dict, parent: str = "") -> dict:
        """Flatten nested dicts from unquoted TOML keys like [env.a.b]."""
        items = []
        for k, v in d.items():
            new_key = f"{parent}.{k}" if parent else k
            # Heuristic: if it's a dict and has no known prompt keys, it's a namespace
            if (
                isinstance(v, dict)
                and not any(
                    fk in v
                    for fk in (
                        "template",
                        "model",
                        "extends",
                        "version",
                        "response_schema",
                    )
                )
                and not any(fk.startswith("_") for fk in v)
            ):
                items.extend(self._flatten_toml(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _resolve_paths(
        self, data: dict[str, Any], base_dir: pathlib.Path
    ) -> dict[str, Any]:
        """
        For each supported field, if the value looks like a file/module path,
        resolve it.

        ``template``  – replaced with the file's text content.
        ``variables`` – list of path specs; each item resolved to a file path
                        string so the VariableRegistry can load it later.
        """
        out = dict(data)

        if "template" in out:
            out["template"] = self._read_template(out["template"], base_dir)

        return out

    @staticmethod
    def _read_template(value: Any, base_dir: pathlib.Path) -> Any:
        """
        If *value* is a single-line string that resolves to an existing file,
        return that file's content.  Otherwise return *value* unchanged.
        """
        if not isinstance(value, str) or "\n" in value:
            return value  # already multiline / non-string

        from ..utils import resolve_path_spec

        resolved, _attr = resolve_path_spec(value, base_dir=base_dir)
        if resolved is not None:
            if _attr and resolved.suffix == ".py":
                import importlib.util
                import sys

                spec_mod = importlib.util.spec_from_file_location(
                    resolved.stem, resolved
                )
                if spec_mod and spec_mod.loader:
                    mod = importlib.util.module_from_spec(spec_mod)
                    sys.path.insert(0, str(resolved.parent))
                    try:
                        spec_mod.loader.exec_module(mod)
                        obj = mod
                        for part in _attr.split("."):
                            obj = getattr(obj, part, None)
                            if obj is None:
                                break
                        if isinstance(obj, str):
                            return obj
                    except Exception:
                        pass
                    finally:
                        sys.path.pop(0)

            try:
                return resolved.read_text(encoding="utf-8")
            except Exception:
                pass
        return value
