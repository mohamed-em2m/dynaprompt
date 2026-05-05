from __future__ import annotations

from typing import Any

from ..nodes import PromptNode


class PromptStore:
    """Manages PromptNode instantiation, history tracking, and caching."""

    def __init__(self, cache_enabled: bool = True):
        self._cache_enabled = cache_enabled
        self._cache: dict[str, PromptNode] = {}
        self._history: dict[str, list[tuple]] = {}
        self._store: dict[str, Any] = {}

    def update_store(self, data: dict[str, Any]):
        self._store = data
        self.clear_cache()

    def clear_cache(self):
        self._cache.clear()

    def __contains__(self, name: str) -> bool:
        return name in self._store

    def __iter__(self):
        return iter(self._store)

    def keys(self):
        return self._store.keys()

    def items(self):
        return self._store.items()

    def __getitem__(self, name: str):
        return self._store[name]

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._store == other
        if isinstance(other, PromptStore):
            return self._store == other._store
        return False

    def get_history(self, name: str | None = None) -> dict:
        if name:
            entries = self._history.get(name, [])
            return [{**src._asdict(), "value": data} for src, data in entries]
        return {
            pname: [{**src._asdict(), "value": data} for src, data in entries]
            for pname, entries in self._history.items()
        }

    def record_history(self, name: str, source: Any, data: dict[str, Any]):
        self._history.setdefault(name, []).append((source, data))

    def get_node(self, name: str, context: dict[str, Any]) -> PromptNode:
        """Create or return a cached PromptNode."""
        if self._cache_enabled and name in self._cache:
            return self._cache[name].copy()

        if name not in self._store:
            available = list(self._store.keys())
            raise AttributeError(
                f"Prompt '{name}' not found. Available prompts: {available}"
            )

        data = dict(self._store[name])
        # Inheritance resolution
        parent_template: str | None = None
        extends = data.get("extends")
        if extends and extends in self._store:
            from ..utils import object_merge

            parent_data = dict(self._store[extends])
            parent_template = parent_data.pop("template", "")
            merged_data = dict(parent_data)
            object_merge(merged_data, data)
            data = merged_data

        template_str = data.pop("template", "")

        # Schema resolution
        schema_name_or_class = data.pop(
            "response_schema", data.pop("_response_schema", None)
        )
        response_schema = (
            context["schemas"].get(schema_name_or_class)
            if isinstance(schema_name_or_class, str)
            else schema_name_or_class
        )

        node = PromptNode(
            name=name,
            text=template_str,
            metadata=data,
            response_schema=response_schema,
            parent_template=parent_template,
            history=self._history.get(name, []),
            variables=context["variables"],
            validators=context["validators"],
            hooks=context["hooks"],
            current_env=context["current_env"],
            auto_render=context["auto_render"],
        )

        if self._cache_enabled:
            self._cache[name] = node

        return node.copy()
