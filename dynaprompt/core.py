"""
DynaPrompt core — LazyPrompts + _PromptSettings.

Inspired by Dynaconf's LazySettings / Settings separation:
- DynaPrompt is the lazy shell (no I/O at creation time).
- _PromptSettings is the real loaded object, instantiated on first access.
"""

from __future__ import annotations

import os
import pathlib
import warnings
from contextlib import contextmanager
from typing import Any

from .engine.layer import EnvLayer
from .engine.registry import VariableRegistry
from .engine.resolver import FileResolver
from .engine.store import PromptStore
from .hooking import Hook
from .loaders import get_loader_for
from .nodes import PromptNode, SourceMetadata
from .utils import object_merge
from .validator import PromptValidator, ValidatorList

_SUPPORTED_SUFFIXES = (".toml", ".md", ".txt", ".py", ".json", ".yaml", ".yml")


class PromptNamespace:
    """Provides dot-notation access to nested prompts."""

    def __init__(self, prefix: str, prompts_instance: DynaPrompt):
        self._prefix = prefix
        self._prompts = prompts_instance

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)

        full_name = f"{self._prefix}.{name}"

        # Try to get it as a direct prompt
        try:
            return self._prompts._wrapped.get(full_name)
        except AttributeError:
            pass

        # Check if it's a further nested namespace
        prefix_dot = f"{full_name}."
        if any(k.startswith(prefix_dot) for k in self._prompts._wrapped._store):
            return PromptNamespace(full_name, self._prompts)

        raise AttributeError(f"Namespace '{self._prefix}' has no attribute '{name}'")

    def __dir__(self) -> list[str]:
        prefix_dot = f"{self._prefix}."
        keys = set()
        for k in self._prompts._wrapped._store:
            if k.startswith(prefix_dot):
                sub = k[len(prefix_dot) :].split(".")[0]
                keys.add(sub)
        return sorted(list(keys) + super().__dir__())


class _PromptSettings:
    """
    The real settings object. Orchestrates FileResolver, VariableRegistry,
    EnvLayer, and PromptStore.
    """

    def __init__(
        self,
        settings_files: list[Any],
        current_env: str = "development",
        file_prefix: str | None = None,
        schemas: dict[str, Any] | None = None,
        variables: list[Any] | None = None,
        auto_render: bool = True,
        structure_mode: bool = True,
    ):
        self._resolver = FileResolver(
            file_prefix=file_prefix, structure_mode=structure_mode
        )
        self._registry = VariableRegistry(auto_render=auto_render, schemas=schemas)
        self._layer = EnvLayer(current_env=current_env)
        self._store = PromptStore(cache_enabled=True)

        self._schemas = schemas if schemas is not None else {}
        self._raw_data: dict[str, dict[str, Any]] = {}
        self._validators = ValidatorList()
        self._hooks: dict[str, list[Hook]] = {}
        self._auto_render = auto_render

        # 1. Variables
        self._registry.load(variables, current_env)

        # 2. Files
        self._load_all(settings_files)

        # 3. Resolve
        self._resolve()

    def _load_all(self, settings_files: list[Any]):
        resolved_items, explicit_files = self._resolver.resolve_all(settings_files)

        for idx, item in enumerate(resolved_items):
            if isinstance(item, dict):
                self._registry.register_dict(
                    item, f"settings_dict_{idx}", "settings", self._layer.current_env
                )
                continue

            path = item
            if path.is_dir():
                self._load_dir(path)
                # Companion TOML
                companion = (path.parent / f"{path.name}.toml").resolve()
                if companion.exists() and companion not in explicit_files:
                    self._load_one_file(companion)
            elif path.exists():
                if path.suffix == ".py":
                    self._load_python_schemas(path)
                elif path.suffix == ".json":
                    self._load_json_schema(path)
                    self._registry.load_from_file(path, self._layer.current_env)
                elif path.suffix in (".yaml", ".yml"):
                    self._load_yaml_schema(path)
                    self._registry.load_from_file(path, self._layer.current_env)
                else:
                    self._load_one_file(path)
            else:
                warnings.warn(
                    f"DynaPrompt: Settings file not found: {item}",
                    UserWarning,
                    stacklevel=3,
                )

    def _load_dir(self, directory: pathlib.Path):
        files_to_load = self._resolver.scan_directory(directory, _SUPPORTED_SUFFIXES)
        for child, sanitized in files_to_load:
            if child.suffix == ".py":
                self._load_python_schemas(child)
            elif child.suffix == ".json":
                self._load_json_schema(child)
                self._registry.load_from_file(child, self._layer.current_env)
            elif child.suffix in (".yaml", ".yml"):
                self._load_yaml_schema(child)
                self._registry.load_from_file(child, self._layer.current_env)
            else:
                self._load_one_file(child, override_name=sanitized)

    def _load_one_file(self, path: pathlib.Path, override_name: str | None = None):
        loader = get_loader_for(path)
        raw = loader.load(path)

        for env, prompts in raw.items():
            if override_name and len(prompts) == 1:
                original = next(iter(prompts))
                if original != override_name:
                    prompts = {override_name: prompts[original]}

            self._raw_data.setdefault(env, {})
            for name, data in prompts.items():
                source = SourceMetadata(
                    loader=loader.__class__.__name__,
                    identifier=str(path),
                    env=env,
                )
                self._store.record_history(name, source, data)
                self._raw_data[env].setdefault(name, {})
                object_merge(self._raw_data[env][name], data)

    def _load_python_schemas(self, path: pathlib.Path):
        # We want schemas to be both in _schemas and in VariableRegistry
        # VariableRegistry._load_python already handles variables.
        # We manually register classes here.
        import importlib.util
        import inspect
        import sys

        spec = importlib.util.spec_from_file_location(path.stem, path)
        if not spec or not spec.loader:
            return
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(path.parent))
        try:
            spec.loader.exec_module(mod)
            for name in dir(mod):
                if not name.startswith("_"):
                    obj = getattr(mod, name)
                    if (
                        inspect.isclass(obj)
                        and getattr(obj, "__module__", None) == mod.__name__
                    ):
                        self._schemas[name] = obj
            # Also load variables
            self._registry.load_from_file(path, self._layer.current_env)
        finally:
            sys.path.pop(0)

    def _load_json_schema(self, path: pathlib.Path):
        import json

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._schemas[path.stem] = data
        except Exception as e:
            warnings.warn(f"DynaPrompt: Failed to load JSON schema from {path}: {e}")

    def _load_yaml_schema(self, path: pathlib.Path):
        import yaml

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._schemas[path.stem] = data
        except Exception as e:
            warnings.warn(f"DynaPrompt: Failed to load YAML schema from {path}: {e}")

    def _resolve(self):
        merged_data = self._layer.resolve_merged_data(self._raw_data)
        self._store.update_store(merged_data)

    def switch_env(self, env: str):
        self._layer.current_env = env
        self._resolve()

    @property
    def _variables(self) -> dict[str, Any]:
        """Compatibility for tests — proxies to VariableRegistry."""
        return self._registry._variables

    def get(self, name: str) -> PromptNode:
        context = {
            "schemas": self._schemas,
            "variables": self._registry.variables,
            "validators": self._validators,
            "hooks": self._hooks,
            "current_env": self._layer.current_env,
            "auto_render": self._auto_render,
        }
        return self._store.get_node(name, context)

    def get_history(self, name: str | None = None) -> dict:
        return self._store.get_history(name)


class DynaPrompt:
    """
    Lazy-loading prompt configuration manager.
    Inspired by Dynaconf's LazySettings — zero I/O at instantiation.
    """

    def __init__(
        self,
        settings_files: list[Any],
        environments: bool = True,
        env: str | None = None,
        validators: list[PromptValidator] | None = None,
        file_prefix: str | None = None,
        variables: list[Any] | None = None,
        auto_render: bool = True,
        auto_export: str | bool = False,
        structure_mode: bool = True,
    ):
        self._settings_files = settings_files
        self._environments = environments
        self._env = env or os.environ.get("ENV_FOR_DYNAPROMPT", "development")
        self._file_prefix = file_prefix
        self._auto_render = auto_render
        self._auto_export = auto_export
        self._structure_mode = structure_mode
        self._validators = ValidatorList()
        if validators:
            self._validators.extend(validators)
        self._hooks: dict[str, list[Hook]] = {}
        self.schemas: dict[str, Any] = {}
        self._variables = variables
        self._wrapped: _PromptSettings | None = None

    def _setup(self) -> None:
        self._wrapped = _PromptSettings(
            settings_files=self._settings_files,
            current_env=self._env,
            file_prefix=self._file_prefix,
            schemas=self.schemas,
            variables=self._variables,
            auto_render=self._auto_render,
            structure_mode=self._structure_mode,
        )
        self._wrapped._validators = self._validators
        self._wrapped._hooks = self._hooks

        if self._auto_export:
            filepath = (
                "pyprompts.toml"
                if isinstance(self._auto_export, bool)
                else self._auto_export
            )
            self.export_to_toml(filepath)

    def export_to_toml(self, filepath: str = "pyprompts.toml") -> None:
        """Export the loaded prompt structure to a TOML file."""
        from .utils import export_to_toml

        export_to_toml(self, filepath)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if self._wrapped is None:
            self._setup()

        try:
            return self._wrapped.get(name)
        except AttributeError:
            pass

        if name in self.schemas:
            return self.schemas[name]

        # Check if it's a nested namespace
        prefix_dot = f"{name}."
        if any(k.startswith(prefix_dot) for k in self._wrapped._store):
            return PromptNamespace(name, self)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'."
        )

    def __dir__(self) -> list[str]:
        if self._wrapped is None:
            self._setup()
        std_attrs = super().__dir__()

        # Only include top-level prompts and namespaces
        top_level_keys = set()
        for k in self._wrapped._store.keys():
            top_level_keys.add(k.split(".")[0])

        schemas = list(self.schemas.keys())
        return sorted(set(std_attrs + list(top_level_keys) + schemas))

    def get(self, name: str) -> PromptNode:
        return self.__getattr__(name)

    @property
    def current_env(self) -> str:
        return self._env

    @contextmanager
    def using_env(self, env: str):
        if self._wrapped is None:
            self._setup()
        old_env = self._wrapped._layer.current_env
        self._wrapped.switch_env(env)
        self._env = env
        try:
            yield self
        finally:
            self._wrapped.switch_env(old_env)
            self._env = old_env

    def reload(self) -> None:
        self._wrapped = None

    def add_validator(self, *validators: PromptValidator) -> None:
        self._validators.extend(validators)
        if self._wrapped:
            self._wrapped._validators = self._validators

    def add_hook(self, event: str, name_or_hook: Any, hook: Hook | None = None) -> None:
        """Register hooks. Safe to call before or after first access."""
        if hook is None:
            hook = name_or_hook
            key = event
        else:
            name = name_or_hook
            key = f"{event}_{name}"
        self._hooks.setdefault(key, []).append(hook)
        if self._wrapped:
            self._wrapped._hooks = self._hooks

    def inspect(self, name: str | None = None) -> dict:
        if self._wrapped is None:
            self._setup()
        return self._wrapped.get_history(name)
