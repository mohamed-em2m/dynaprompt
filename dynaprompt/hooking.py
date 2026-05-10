"""Lifecycle hooks — inspired by Dynaconf's hookable/post_hook pattern."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable


@dataclass
class Hook:
    """Wraps a callable for a lifecycle event."""

    function: Callable

    def __repr__(self):
        return f"Hook({self.function.__name__})"


class HookValue:
    """Wrapper around a value passed between hooks — same pattern as Dynaconf."""

    def __init__(self, value: Any):
        self.value = value

    def __repr__(self):
        return repr(self.value)


def hookable(function=None, name: str = None):
    """
    Decorator that adds before/after hook dispatch to any method.

    Usage on a class::

        class MyPromptNode:
            @hookable
            def render(self, **kwargs):
                ...

    Then hooks are dispatched from `self._hooks` dict if present.
    """

    def dispatch(fun, self, *args, **kwargs):
        hooks: dict = getattr(self, "_hooks", {})
        fn_name = name or fun.__name__
        obj_name = getattr(self, "name", None)

        # Build list of hooks to run
        # 1. Generic hooks: e.g. 'before_render'
        before_hooks = list(hooks.get(f"before_{fn_name}", []))
        after_hooks = list(hooks.get(f"after_{fn_name}", []))

        # 2. Namespaced hooks: e.g. 'before_render_greet'
        if obj_name:
            before_hooks.extend(hooks.get(f"before_{fn_name}_{obj_name}", []))
            after_hooks.extend(hooks.get(f"after_{fn_name}_{obj_name}", []))

        if not before_hooks and not after_hooks:
            return fun(self, *args, **kwargs)

        # Run before hooks — they can mutate kwargs
        value = HookValue(None)
        for hook in before_hooks:
            # Handle both Hook objects and raw callables
            func = hook.function if hasattr(hook, "function") else hook
            value = HookValue(func(self, value.value, *args, **kwargs))

        # Run real function
        result = fun(self, *args, **kwargs)
        value = HookValue(result)

        # Run after hooks — they can transform the result
        for hook in after_hooks:
            # Handle both Hook objects and raw callables
            func = hook.function if hasattr(hook, "function") else hook
            value = HookValue(func(self, value.value, *args, **kwargs))

        return value.value

    if function:
        # Used as bare @hookable decorator
        @wraps(function)
        def wrapper(*args, **kwargs):
            return dispatch(function, *args, **kwargs)

        return wrapper

    # Used as @hookable(name='...')
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return dispatch(fn, *args, **kwargs)

        return wrapper

    return decorator


def async_hookable(function=None, name: str = None):

    async def dispatch(fun, self, *args, **kwargs):
        hooks: dict = getattr(self, "_hooks", {})
        fn_name = name or fun.__name__
        obj_name = getattr(self, "name", None)

        before_hooks = list(hooks.get(f"before_{fn_name}", []))
        after_hooks = list(hooks.get(f"after_{fn_name}", []))

        if obj_name:
            before_hooks.extend(hooks.get(f"before_{fn_name}_{obj_name}", []))
            after_hooks.extend(hooks.get(f"after_{fn_name}_{obj_name}", []))

        if not before_hooks and not after_hooks:
            return await fun(self, *args, **kwargs)

        value = HookValue(None)
        for hook in before_hooks:
            func = hook.function if hasattr(hook, "function") else hook
            res = func(self, value.value, *args, **kwargs)
            if asyncio.iscoroutine(res):
                res = await res
            value = HookValue(res)

        result = await fun(self, *args, **kwargs)
        value = HookValue(result)

        for hook in after_hooks:
            func = hook.function if hasattr(hook, "function") else hook
            res = func(self, value.value, *args, **kwargs)
            if asyncio.iscoroutine(res):
                res = await res
            value = HookValue(res)

        return value.value

    if function:

        @wraps(function)
        async def wrapper(*args, **kwargs):
            return await dispatch(function, *args, **kwargs)

        return wrapper

    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            return await dispatch(fn, *args, **kwargs)

        return wrapper

    return decorator


def post_render_hook(function: Callable) -> Callable:
    """
    Marks a function as an after_render hook.

    Usage in a prompts config .py file::

        from dynaprompt import post_render_hook

        @post_render_hook
        def redact_secrets(prompt_node, rendered_text, **kwargs):
            return rendered_text.replace(os.environ.get('API_KEY', ''), '***')
    """
    function._dynaprompt_hook = True
    function._hook_type = "after_render"
    return function


def post_load_hook(function: Callable) -> Callable:
    """
    Marks a function as an after_load hook (fires after a prompt file is parsed).

    Usage::

        @post_load_hook
        def normalize_template(prompt_node, text, **kwargs):
            return text.strip()
    """
    function._dynaprompt_hook = True
    function._hook_type = "after_load"
    return function
