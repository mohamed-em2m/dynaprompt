from __future__ import annotations

from typing import Any

from ..utils import object_merge


class EnvLayer:
    """Handles environment layering logic and switching."""

    def __init__(self, current_env: str = "development"):
        self._current_env = current_env

    def resolve_merged_data(
        self, raw_data: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Deep-merge default + current_env layers for every known prompt."""
        all_names: set[str] = set()
        for env_prompts in raw_data.values():
            all_names.update(env_prompts.keys())

        store: dict[str, Any] = {}
        for name in all_names:
            merged: dict[str, Any] = {}
            # Layer 1: default
            default_data = raw_data.get("default", {}).get(name, {})
            object_merge(merged, default_data)
            # Layer 2: current env override
            if self._current_env != "default":
                env_data = raw_data.get(self._current_env, {}).get(name, {})
                object_merge(merged, env_data)
            store[name] = merged
        return store

    @property
    def current_env(self) -> str:
        return self._current_env

    @current_env.setter
    def current_env(self, value: str):
        self._current_env = value
