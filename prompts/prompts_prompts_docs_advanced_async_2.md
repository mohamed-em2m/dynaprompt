# Async Support

DynaPrompt has first-class support for `async`/`await`, making it a natural fit for FastAPI, async agents, and any I/O-heavy Python application.

---

## Why Async Matters for LLMs

Prompt rendering itself is CPU-bound (Jinja2 string processing), but in real applications you often need to:

- Run multiple renders concurrently before dispatching to an LLM
- Use async hooks that call external services (e.g., a secrets vault or PII detector)
- Integrate with async frameworks like **FastAPI**, **LangGraph**, or **CrewAI**

---

## `async_render()`

The async equivalent of `.render()`. Use it anywhere you can `await`:

```python
import asyncio
from dynaprompt import DynaPrompt

prompts = DynaPrompt(settings_files=["prompts/"])

async def main():
    rendered = await prompts.greeting.async_render(
        user_name="Ahmed",
        app_name="TechTrax"
    )
    print(rendered.text)
    print(rendered.prompt_hash)  # SHA-256 hash still included

asyncio.run(main())
```

---

## FastAPI Integration

```python
from fastapi import FastAPI
from dynaprompt import DynaPrompt

app = FastAPI()
prompts = DynaPrompt(settings_files=["prompts/"])

@app.post("/chat")
async def chat(user_name: str, message: str):
    rendered = await prompts.chat.async_render(
        user_name=user_name,
        message=message
    )
    # Send rendered.text to your LLM client
    response = await llm_client.complete(
        model=rendered.config["model"],
        prompt=rendered.text,
    )
    return {
        "response": response,
        "prompt_hash": rendered.prompt_hash,  # log this for debugging!
    }
```

---

## Async Hooks

You can also attach async hooks using `@async_hookable`. This is useful for:
- Calling an async PII redaction service before rendering
- Logging to an async audit trail after rendering

```python
from dynaprompt import DynaPrompt
from dynaprompt.hooking import async_hookable

prompts = DynaPrompt(settings_files=["prompts/"])

async def async_inject_context(node, kwargs):
    # Simulate async call, e.g., fetching user profile from DB
    user_data = await db.get_user(kwargs.get("user_id"))
    kwargs["user_name"] = user_data["name"]
    return kwargs

prompts.add_hook("before_render", "inject_context", async_inject_context)

rendered = await prompts.chat.async_render(user_id="123")
```

---

## `async_rerender()`

Just like `rerender()`, but async. Remembers the kwargs from a previous render:

```python
first = await prompts.translate.async_render(text="Hello", lang="ES")
# Only override 'text', 'lang' is preserved
second = await prompts.translate.async_rerender(text="Goodbye")
```

---

!!! tip "Sync is still supported"
    `async_render()` and `render()` are fully interchangeable. Use sync in scripts and tests, async in web servers and agents.
