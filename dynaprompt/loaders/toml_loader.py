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
        for env_key, prompts in raw.items():
            if not isinstance(prompts, dict):
                continue
            result[env_key] = {}
            for prompt_name, data in prompts.items():
                if isinstance(data, dict):
                    data = self._resolve_paths(data, path.parent)
                    result[env_key][prompt_name] = data

        return result

    # ------------------------------------------------------------------
    # Path resolution helpers
    # ------------------------------------------------------------------

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
            try:
                return resolved.read_text(encoding="utf-8")
            except Exception:
                pass
        return value
