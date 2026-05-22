"""PromptNode and RenderedPrompt — the core data nodes."""

from __future__ import annotations

import datetime
import os
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

import jinja2
from pydantic import BaseModel

from .hooking import async_hookable, hookable
from .secrets import SecretStore
from .validator import ValidatorList

_render_stack: ContextVar[frozenset[str]] = ContextVar(
    "_render_stack", default=frozenset()
)


@dataclass
class SourceMetadata:
    """Tracks where a prompt was loaded from — for audit and rollback."""

    loader: str
    identifier: str
    env: str = "default"
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now().isoformat(timespec="seconds")
    )

    def _asdict(self) -> dict:
        return {
            "loader": self.loader,
            "identifier": self.identifier,
            "env": self.env,
            "timestamp": self.timestamp,
        }


@dataclass
class RenderedPrompt:
    """The final output of PromptNode.render() — fully interpolated text + config."""

    text: str
    config: dict[str, Any]
    response_schema: type[BaseModel] | None = None
    source_history: list[tuple] = field(default_factory=list)
    prompt_hash: str = ""

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        preview = self.text[:80].replace("\n", " ")
        return f"RenderedPrompt(text={preview!r}..., model={self.config.get('model')})"

    @property
    def schema_dict(self) -> dict:
        """Returns the response_schema as a JSON Schema dictionary."""
        if not self.response_schema:
            return {}
        if isinstance(self.response_schema, dict):
            return self.response_schema
        try:
            return self.response_schema.model_json_schema()
        except AttributeError:
            if hasattr(self.response_schema, "schema"):
                return self.response_schema.schema()
            return {}

    @property
    def schema_json(self) -> str:
        """Returns the response_schema as a formatted JSON Schema string."""
        import json

        return json.dumps(self.schema_dict, indent=2)


class VariableDict(dict):
    """A dictionary that allows dot-notation access to its keys."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(f"'VariableDict' object has no attribute '{name}'")


class PromptsProxy:
    """Lazy loader for other prompts within a Jinja context."""

    def __init__(self, store: Any, parent_context: dict[str, Any]):
        self._store = store
        self._parent_context = parent_context
        self._cache: dict[str, PromptNode] = {}

    def __getitem__(self, name: str) -> Any:
        if name in self._cache:
            return self._cache[name]

        if not self._store or name not in self._store:
            raise KeyError(name)

        node = self._store.get_node(name, self._parent_context)
        self._cache[name] = node
        return node

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"Prompt '{name}' not found in store.")


class PromptNode:
    """
    Represents a single parsed prompt. Supports fluent config overrides and
    Jinja2 rendering with secret injection.
    """

    def __init__(
        self,
        name: str,
        text: str,
        metadata: dict[str, Any] = None,
        response_schema: type[BaseModel] | None = None,
        parent_template: str | None = None,
        history: list[tuple] = None,
        variables: dict[str, Any] = None,
        validators: ValidatorList = None,
        hooks: dict[str, list] = None,
        current_env: str = "default",
        auto_render: bool = False,
        store: Any = None,
        parent_context: dict[str, Any] = None,
    ):
        self.name = name
        self.text = text
        self.raw_template = text
        self.metadata = metadata or {}
        self.response_schema = response_schema
        self._parent_template = parent_template
        self._history = history or []
        self.variables = VariableDict(variables or {})
        self._validators = validators or ValidatorList()
        self._hooks = hooks or {}
        self._current_env = current_env
        self._auto_render = auto_render
        self._store = store
        self._parent_context = parent_context
        self._overrides: dict[str, Any] = {}
        self.bound_kwargs: dict[str, Any] = {}

        if self.response_schema is None:
            try:
                from pydantic import BaseModel

                # Auto-detect Pydantic schemas referenced in the template text
                pydantic_models = [
                    v
                    for k, v in self.variables.items()
                    if isinstance(v, type)
                    and issubclass(v, BaseModel)
                    and k in self.raw_template
                ]
                if len(pydantic_models) == 1:
                    self.response_schema = pydantic_models[0]
            except ImportError:
                pass

        self._setup_template()

    def __str__(self) -> str:
        """Auto-render when used in a string context (e.g. nested prompts)."""
        return self.render().text

    def _setup_template(self) -> None:
        """Pre-compile Jinja2 template and handle auto-rendering."""
        jinja_env = jinja2.Environment(undefined=jinja2.Undefined)
        jinja_env_async = jinja2.Environment(
            undefined=jinja2.Undefined, enable_async=True
        )
        template_str = self.raw_template
        if self._parent_template and "{{ super() }}" in template_str:
            template_str = template_str.replace("{{ super() }}", self._parent_template)

        self._compiled_template = jinja_env.from_string(template_str)
        self._compiled_template_async = jinja_env_async.from_string(template_str)

        if self._auto_render:
            try:
                # Use internal render to benefit from recursion stack protection
                # while avoiding triggering lifecycle hooks during initialization.
                rendered = self._render_internal()
                self.text = rendered.text
            except Exception as exc:
                import warnings

                warnings.warn(
                    f"DynaPrompt: Failed to auto-render prompt '{self.name}': {exc}",
                    UserWarning,
                    stacklevel=2,
                )

    @property
    def template(self) -> str:
        """Returns the raw, unrendered template string."""
        return self.raw_template

    @template.setter
    def template(self, value: str) -> None:
        self.raw_template = value
        self.text = value
        self._setup_template()

    def _build_render_context(
        self, extra_kwargs: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Build the full Jinja2 rendering context including secrets, env,
        globals, metadata, and schemas.
        """
        extra_kwargs = extra_kwargs or {}
        context = {
            "secrets": SecretStore(),
            "env": os.environ.get,
            "today": datetime.date.today().isoformat(),
            "current_env": self._current_env,
        }

        def inject_and_flatten(source_dict):
            if not source_dict:
                return
            context.update(source_dict)
            for vkey in ("variables", "vars"):
                if vkey in source_dict and isinstance(source_dict[vkey], dict):
                    # Recursive flatten of this specific source's variables
                    def flatten(d):
                        for k, v in d.items():
                            context[k] = v
                            if isinstance(v, dict):
                                flatten(v)

                    flatten(source_dict[vkey])

        # 1. Global variables
        inject_and_flatten(self.variables)

        # 2. Prompt metadata (frontmatter)
        inject_and_flatten(self.metadata)

        # 3. Render-time keyword arguments
        inject_and_flatten(extra_kwargs)

        # 4. Nested prompts support
        if self._store:
            # Provide explicit 'prompts' accessor
            proxy = PromptsProxy(self._store, self._parent_context)
            context["prompts"] = proxy

            # Inject top-level names lazily via property-like behavior isn't easy
            # in a dict, so we'll just inject them all. To avoid the RecursionError
            # during auto_render, we rely on the _render_stack check in render().
            for p_name in self._store.keys():
                if p_name != self.name and p_name not in context:
                    # We inject the proxy indexer itself? No, Jinja needs the object.
                    # But if we access it now, it triggers render().
                    # However, render() is now protected!
                    try:
                        context[p_name] = proxy[p_name]
                    except (KeyError, AttributeError):
                        pass

        # 5. Global schemas support
        if self._parent_context and "schemas" in self._parent_context:
            for s_name, s_obj in self._parent_context["schemas"].items():
                if s_name not in context:
                    context[s_name] = s_obj

        # Auto-inject JSON schema if a response_schema was resolved
        if self.response_schema:
            context["response_schema"] = self.schema_json

        # Auto-serialize Pydantic models (classes or instances) to JSON/dict
        import inspect
        import json

        def _deep_process(obj, key_name=""):
            # 1. Pydantic Classes (Schemas) -> JSON String
            if inspect.isclass(obj):
                if hasattr(obj, "model_json_schema"):
                    return json.dumps(obj.model_json_schema(), indent=2)
                if hasattr(obj, "schema"):
                    return json.dumps(obj.schema(), indent=2)
                return obj

            # 2. Pydantic Instances -> Dict (for template access) or JSON
            # (if key suggests)
            if hasattr(obj, "model_dump"):  # Pydantic v2
                if "json" in key_name.lower() or "schema" in key_name.lower():
                    return obj.model_dump_json(indent=2)
                return obj.model_dump()
            if hasattr(obj, "dict") and callable(obj.dict):  # Pydantic v1
                if "json" in key_name.lower() or "schema" in key_name.lower():
                    return obj.json(indent=2)
                return obj.dict()

            # 3. Recursive containers
            if isinstance(obj, dict):
                return {k: _deep_process(v, k) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_deep_process(v, key_name) for v in obj]

            # 4. Standard JSON fallback for dict/list if key suggests
            if isinstance(obj, (dict, list)) and (
                "schema" in key_name.lower() or "json" in key_name.lower()
            ):
                try:
                    return json.dumps(obj, indent=2)
                except Exception:
                    return obj

            return obj

        for k, v in list(context.items()):
            if k in ("secrets", "env", "today", "current_env"):
                continue
            context[k] = _deep_process(v, k)

        return context

    # ─── Fluent API ───────────────────────────────────────────────────────────

    def with_model(self, model: str) -> PromptNode:
        self._overrides["model"] = model
        return self

    def with_temperature(self, temperature: float) -> PromptNode:
        self._overrides["temperature"] = temperature
        return self

    def with_max_tokens(self, max_tokens: int) -> PromptNode:
        self._overrides["max_tokens"] = max_tokens
        return self

    def with_schema(self, schema: type[BaseModel]) -> PromptNode:
        self.response_schema = schema
        return self

    def copy(self) -> PromptNode:
        """Return a fresh copy of this node to avoid cross-request state pollution."""
        import copy

        new_node = copy.copy(self)
        # Deep copy the mutable state containers
        new_node._overrides = self._overrides.copy()
        new_node.bound_kwargs = self.bound_kwargs.copy()
        return new_node

    # ─── Rendering ────────────────────────────────────────────────────────────

    def _compute_hash(self, text: str, config: dict) -> str:
        """Computes a stable hash for the rendered prompt."""
        import hashlib

        hash_input = f"{text}:{config}:{self.schema_json}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:12]

    @hookable
    def render(self, *args, **kwargs) -> RenderedPrompt:
        """
        Render the prompt template with the provided variables.
        Runs validators → Jinja2 → after_render hooks.
        """
        return self._render_internal(*args, **kwargs)

    def _render_internal(self, *args, **kwargs) -> RenderedPrompt:
        """Core rendering logic with recursion protection but no hooks."""
        stack = _render_stack.get()
        if self.name in stack:
            # Short-circuit recursion by returning a notice instead of failing
            msg = f"[Recursive reference to '{self.name}' detected]"
            return RenderedPrompt(text=msg, config={})

        token = _render_stack.set(stack | {self.name})
        try:
            for arg in args:
                if isinstance(arg, dict):
                    kwargs.update(arg)

            self.bound_kwargs.update(kwargs)

            self._validators.validate(
                self, self.bound_kwargs, current_env=self._current_env
            )

            context = self._build_render_context(self.bound_kwargs)

            try:
                rendered_text = self._compiled_template.render(**context)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to render prompt '{self.name}': {exc}"
                ) from exc

            final_config = {**self.metadata, **self._overrides}
            p_hash = self._compute_hash(rendered_text, final_config)

            return RenderedPrompt(
                text=rendered_text,
                config=final_config,
                response_schema=self.response_schema,
                source_history=self._history,
                prompt_hash=p_hash,
            )
        finally:
            _render_stack.reset(token)


    @async_hookable
    async def async_render(self, *args, **kwargs) -> RenderedPrompt:
        """
        Asynchronously render the prompt template (I/O non-blocking).
        Runs validators → Jinja2 async → after_render hooks.
        """
        return await self._async_render_internal(*args, **kwargs)

    async def _async_render_internal(self, *args, **kwargs) -> RenderedPrompt:
        """Core async rendering logic with recursion protection but no hooks."""
        stack = _render_stack.get()
        if self.name in stack:
            msg = f"[Recursive reference to '{self.name}' detected]"
            return RenderedPrompt(text=msg, config={})

        token = _render_stack.set(stack | {self.name})
        try:
            for arg in args:
                if isinstance(arg, dict):
                    kwargs.update(arg)

            self.bound_kwargs.update(kwargs)

            self._validators.validate(
                self, self.bound_kwargs, current_env=self._current_env
            )

            context = self._build_render_context(self.bound_kwargs)

            try:
                rendered_text = await self._compiled_template_async.render_async(**context)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to async-render prompt '{self.name}': {exc}"
                ) from exc

            final_config = {**self.metadata, **self._overrides}
            p_hash = self._compute_hash(rendered_text, final_config)

            return RenderedPrompt(
                text=rendered_text,
                config=final_config,
                response_schema=self.response_schema,
                source_history=self._history,
                prompt_hash=p_hash,
            )
        finally:
            _render_stack.reset(token)

    def rerender(self, **kwargs) -> RenderedPrompt:
        """
        Alias for render(). Useful for explicitly updating a subset of previously
        provided variables while retaining the rest.
        """
        return self.render(**kwargs)

    async def async_rerender(self, **kwargs) -> RenderedPrompt:
        """Async alias for rerender()."""
        return await self.async_render(**kwargs)

    def call(self, **kwargs) -> Any:
        """
        Render and (in the future) call an LLM provider directly.
        """
        raise NotImplementedError(
            "LLM invocation not yet implemented — use render() and call your "
            "LLM client directly."
        )

    def __repr__(self) -> str:
        preview = self.text[:60].replace("\n", " ")
        return (
            f"PromptNode(name={self.name!r}, "
            f"model={self.metadata.get('model')!r}, "
            f"template={preview!r}...)"
        )

    @property
    def schema_dict(self) -> dict:
        """Returns the response_schema as a JSON Schema dictionary."""
        if not self.response_schema:
            return {}
        if isinstance(self.response_schema, dict):
            return self.response_schema
        try:
            return self.response_schema.model_json_schema()
        except AttributeError:
            if hasattr(self.response_schema, "schema"):
                return self.response_schema.schema()
            return {}

    @property
    def schema_json(self) -> str:
        """Returns the response_schema as a formatted JSON Schema string."""
        import json

        return json.dumps(self.schema_dict, indent=2)
