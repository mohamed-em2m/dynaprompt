# Environment Layering

One of DynaPrompt's most powerful features is its **environment layering** system. It lets you define base prompts once and override specific values per environment — without duplicating entire templates.

---

## How It Works

DynaPrompt uses a **deep merge** strategy. Values defined in a specific environment layer override the defaults, while everything else is inherited.

```
[default]    <-- Base values, always applied
     ↓
[development]  or  [production]  or  [staging]   <-- Overrides
     ↓
ENV Variables  (highest priority)
```

---

## TOML Example

```toml title="prompts.toml"
# Base configuration — applies to all environments
[default.analyzer]
template = "prompts/analyze.md"
model = "gpt-3.5-turbo"
temperature = 0.3
max_tokens = 1024

# Production gets a more powerful model with stricter settings
[production.analyzer]
model = "gpt-4o"
temperature = 0.1
max_tokens = 4096
```

```python
from dynaprompt import DynaPrompt

# Development — uses gpt-3.5-turbo
dev_prompts = DynaPrompt(settings_files=["prompts.toml"], env="development")
print(dev_prompts.analyzer.metadata["model"])  # gpt-3.5-turbo

# Production — uses gpt-4o
prod_prompts = DynaPrompt(settings_files=["prompts.toml"], env="production")
print(prod_prompts.analyzer.metadata["model"])  # gpt-4o
```

---

## Switching Environments at Runtime

Use the `using_env()` context manager to temporarily switch environments without creating a new `DynaPrompt` instance:

```python
prompts = DynaPrompt(settings_files=["prompts.toml"], env="development")

# Normal — uses development settings
rendered = prompts.analyzer.render(transcript="...")
print(rendered.config["model"])  # gpt-3.5-turbo

# Temporarily switch to production
with prompts.using_env("production"):
    rendered = prompts.analyzer.render(transcript="...")
    print(rendered.config["model"])  # gpt-4o

# Back to development
rendered = prompts.analyzer.render(transcript="...")
print(rendered.config["model"])  # gpt-3.5-turbo
```

---

## Environment via ENV Variable

You can also set the environment via an environment variable — ideal for Docker/Kubernetes deployments:

```bash
export ENV_FOR_DYNAPROMPT=production
```

```python
# Will automatically use "production" layer
prompts = DynaPrompt(settings_files=["prompts/"])
```

---

## Debug: Who Provided That Value?

Use `debug_trace()` to see exactly which layer each configuration value came from:

```python
prompts.debug_trace("analyzer")
```

**Output:**
```
🔍 Debug Trace for: analyzer
──────────────────────────────────
Layer: default
  model        = gpt-3.5-turbo
  temperature  = 0.3

Layer: production  ← ACTIVE
  model        = gpt-4o         ✅ overrides default
  temperature  = 0.1            ✅ overrides default

Final merged config:
  model        = gpt-4o
  temperature  = 0.1
  max_tokens   = 1024  (from default)
──────────────────────────────────
```

---

!!! tip "Environment names are arbitrary"
    You can define any environment name — `staging`, `eu-west`, `canary`, `testing`. The only reserved name is `default`.
