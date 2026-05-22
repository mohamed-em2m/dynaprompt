# Debugging & Tracing

DynaPrompt provides built-in tools to help you understand exactly what was loaded, where it came from, and which layer won a merge.

---

## `inspect()` — Loading Summary

`inspect()` prints a summary of all loaded prompts and their sources. Call it after initialization to verify everything loaded correctly:

```python
prompts = DynaPrompt(settings_files=["prompts/"])
prompts.inspect()
```

**Output:**
```
📚 DynaPrompt — Loaded Prompts
─────────────────────────────────────
  ✔ greeting          prompts/greeting.md
  ✔ support.chat      prompts/support/chat.toml
  ✔ analyzer          prompts/analyze.md
─────────────────────────────────────
Total: 3 prompt(s) loaded
```

---

## `debug_trace()` — Merge Hierarchy

Use `debug_trace(name)` to see the full merge hierarchy for a specific prompt — which environment layers exist and which values each provides:

```python
prompts.debug_trace("analyzer")
```

This is the most useful tool when a prompt is behaving unexpectedly and you need to know **which layer is winning**.

---

## Introspection Methods

DynaPrompt exposes several methods for programmatic introspection:

```python
# List all prompt keys
prompts.keys()          # ['greeting', 'support.chat', 'analyzer']

# Iterate over all prompts
for name in prompts:
    print(name)

# Access all prompts as a dict of PromptNode objects
all_prompts = prompts.prompts
# {'greeting': <PromptNode>, 'support.chat': <PromptNode>, ...}
```

---

## Prompt Hashing for Audit Trails

Every `RenderedPrompt` includes a **SHA-256 hash** of the rendered text. This lets you:

- Detect when a prompt template changes between deployments
- Log exact prompt versions alongside LLM responses (for LangSmith, MLflow, etc.)
- Build deterministic test assertions

```python
rendered = prompts.analyzer.render(transcript="Hello world")

print(rendered.prompt_hash)
# → "a3f1c2d4e5b6..." (SHA-256 of rendered.text)

# Store alongside your LLM call log
log_entry = {
    "model": rendered.config["model"],
    "prompt_hash": rendered.prompt_hash,
    "response": llm_response,
    "timestamp": datetime.utcnow().isoformat()
}
```

---

## `reload()` — Force Reload from Disk

If you're iterating on prompt files and don't want to restart your app:

```python
prompts.reload()
```

This clears the internal cache and re-reads all files on the next access.

---

!!! note "Tab completion in notebooks"
    In Jupyter and IPython, `DynaPrompt` supports tab completion. Type `prompts.` and press Tab to see all available prompts.
