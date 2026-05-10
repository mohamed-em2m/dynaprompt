from __future__ import annotations

import pathlib
import warnings
from typing import Any

from ..utils import object_merge


class VariableRegistry:
    """Handles global variable loading, namespacing, and merging."""

    def __init__(
        self, auto_render: bool = False, schemas: dict[str, Any] | None = None
    ):
        self._variables: dict[str, Any] = {}
        self._auto_render = auto_render
        self._schemas = schemas if schemas is not None else {}

    def load(self, items: list[Any] | None, current_env: str = "default") -> None:
        if not items:
            return

        for idx, item in enumerate(items):
            if isinstance(item, dict):
                warnings.warn(
                    "DynaPrompt: Merging direct dictionary into variables. "
                    "Keys already present will be disambiguated by source tag.",
                    UserWarning,
                    stacklevel=3,
                )
                self.register_dict(item, f"dict_{idx}", "dict", current_env)
            elif isinstance(item, (str, pathlib.Path)):
                self._load_flexible(item, current_env)

    def register_dict(
        self,
        data: dict[str, Any],
        container_key: str,
        source_tag: str,
        current_env: str = "default",
    ) -> None:
        # Handle environment layering if present
        is_env_layered = "default" in data and isinstance(data["default"], dict)

        if is_env_layered:
            final_data: dict[str, Any] = {}
            object_merge(final_data, data.get("default", {}))
            env_data = data.get(current_env)
            if isinstance(env_data, dict):
                object_merge(final_data, env_data)
            data = final_data

        # 1. Whole object
        self.set_var(container_key, data, source_tag)

        # 2. Flatten
        def _flatten(d: dict[str, Any]):
            for k, v in d.items():
                self.set_var(k, v, source_tag)
                if isinstance(v, dict):
                    _flatten(v)

        _flatten(data)

    def set_var(self, key: str, value: Any, source_tag: str) -> None:
        if self._auto_render and isinstance(value, str) and "{{" in value:
            try:
                import jinja2

                jinja_env = jinja2.Environment(undefined=jinja2.Undefined)
                value = jinja_env.from_string(value).render(**self._variables)
            except Exception as e:
                warnings.warn(
                    f"DynaPrompt: Failed to auto-render variable '{key}': {e}",
                    UserWarning,
                    stacklevel=5,
                )

        if key in self._variables and self._variables[key] is not value:
            namespaced = f"{key}_{source_tag}"
            if (
                namespaced in self._variables
                and self._variables[namespaced] is not value
            ):
                warnings.warn(
                    f"DynaPrompt: Variable '{key}' already exists from a different "
                    f"source. Both '{key}' and '{namespaced}' already set — skipping.",
                    UserWarning,
                    stacklevel=4,
                )
                return
            warnings.warn(
                f"DynaPrompt: Variable '{key}' already exists. "
                f"Saving as '{namespaced}' to avoid overwriting the original.",
                UserWarning,
                stacklevel=4,
            )
            self._variables[namespaced] = value
        else:
            self._variables[key] = value

    def _load_flexible(self, spec: str | pathlib.Path, current_env: str) -> None:
        """Resolve a flexible path spec and load variables from it.

        Supports all formats handled by ``resolve_path_spec``::

            "config/var.py"              → load whole file
            "config/var.py:variables"    → load only that attribute
            "config.var.variables"       → dotted module + attribute
            "config.var"                 → dotted module, whole file
            "config/var"                 → auto-detect extension
        """
        # If it's already a resolved Path, skip the spec resolution
        if isinstance(spec, pathlib.Path):
            path = spec.resolve()
            if path.exists():
                self.load_from_file(path, current_env)
            else:
                warnings.warn(
                    f"DynaPrompt: Variables file not found: {path}",
                    UserWarning,
                    stacklevel=3,
                )
            return

        from ..utils import resolve_path_spec

        resolved_path, attr_name = resolve_path_spec(spec)

        if resolved_path is None:
            # Fallback: try as a plain path
            plain = pathlib.Path(spec).resolve()
            if plain.exists():
                self.load_from_file(plain, current_env)
            else:
                warnings.warn(
                    f"DynaPrompt: Could not resolve variables spec: {spec!r}",
                    UserWarning,
                    stacklevel=3,
                )
            return

        if attr_name and resolved_path.suffix == ".py":
            # Load only a specific attribute from the Python module
            self._load_python_attr(resolved_path, attr_name)
        else:
            self.load_from_file(resolved_path, current_env)

    def _load_python_attr(self, path: pathlib.Path, attr_name: str) -> None:
        """Load a specific attribute from a Python module as a variable."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(path.stem, path)
        if not spec or not spec.loader:
            return
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(path.parent))
        try:
            spec.loader.exec_module(mod)
            # Navigate dotted attrs: "variables" or "nested.attr"
            obj = mod
            for part in attr_name.split("."):
                obj = getattr(obj, part, None)
                if obj is None:
                    warnings.warn(
                        f"DynaPrompt: Attribute '{attr_name}' not found in {path}",
                        UserWarning,
                        stacklevel=3,
                    )
                    return

            if isinstance(obj, dict):
                self.register_dict(obj, f"{path.stem}_{attr_name}", "py", "default")
            else:
                self.set_var(attr_name, obj, "py")
        finally:
            sys.path.pop(0)

    def load_from_file(self, path: pathlib.Path, current_env: str) -> None:
        suffix = path.suffix.lower()
        source_tag = path.stem

        try:
            if suffix == ".py":
                self._load_python(path)
                return

            if suffix == ".json":
                import json

                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                tag = "json"
            elif suffix in (".yaml", ".yml"):
                import yaml

                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                tag = "yaml"
            elif suffix == ".toml":
                data = self._load_toml(path)
                tag = "toml"
            else:
                return

            if not isinstance(data, dict):
                return

            self.register_dict(data, source_tag, tag, current_env)

        except Exception as e:
            warnings.warn(f"DynaPrompt: Failed to load variables from '{path}': {e}")

    def _load_python(self, path: pathlib.Path) -> None:
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(path.stem, path)
        if not spec or not spec.loader:
            return
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(path.parent))
        try:
            spec.loader.exec_module(mod)
            import inspect

            for name in dir(mod):
                if not name.startswith("_"):
                    obj = getattr(mod, name)
                    # Only register names actually defined in this module
                    origin = getattr(obj, "__module__", None)
                    if origin is not None and origin != mod.__name__:
                        continue

                    if inspect.isclass(obj):
                        self._schemas[name] = obj

                    self.set_var(name, obj, "py")
        finally:
            sys.path.pop(0)

    def _load_toml(self, path: pathlib.Path) -> dict:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        with open(path, "rb") as f:
            return tomllib.load(f)

    @property
    def variables(self) -> dict[str, Any]:
        return self._variables
