<p align="center"><img src="/art/dynaprompt .png" alt="dynaprompt  logo"></p>

> **dynaprompt ** - Lazy-loading prompt configuration manager built directly on Dynaconf's principles.

[![MIT License](https://img.shields.io/badge/license-MIT-007EC7.svg?style=flat-square)](/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/dynaprompt .svg)](https://pypi.python.org/pypi/dynaprompt )
[![Code Style Black](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Coverage](https://img.shields.io/badge/coverage-71%25-green.svg)](/tests)

DynaPrompt is a powerful, lazy-loading prompt configuration manager inspired by Dynaconf. It offers a structured way to manage, version, and render LLM prompts while separating prompt text from configuration metadata.

## 🚀 30-Second Quickstart

```bash
pip install dynaprompt
```

1. Create a `prompts.toml`:
```toml
[default.greeting]
template = "Hello {{ name }}! You are a helpful assistant."

[production.greeting]
template = "Hello {{ name }}! You are a professional consultant."
```

2. Use it in Python:
```python
from dynaprompt import DynaPrompt

prompts = DynaPrompt(settings_files=["prompts.toml"])

# Renders: "Hello Emam! You are a helpful assistant."
print(prompts.greeting.render(name="Emam").text)
```

---

## 💡 Why DynaPrompt?

### 1. Lazy Loading is the Core
Most libraries load prompts at import time. This makes environment swapping hard and slows down startup.

**The "Old" Way (Hardcoded/Manual):**
```python
# Loaded once, forever. Hard to swap for tests/production.
SYSTEM_PROMPT = open("prompts/system.txt").read()
```

**The DynaPrompt Way:**
```python
from dynaprompt import prompts
# File is only read NOW. Respects ENV_FOR_DYNAPROMPT=production automatically.
print(prompts.system.render())
```

### 2. Why not just use Dynaconf?
Since Dynaconf handles strings, why a new library? DynaPrompt adds **prompt-specific** logic:
- **Jinja2 First-Class**: Automatic variable injection, recursive flattening, and secret resolution.
- **Schema Auto-loading**: Automatically registers Pydantic models from `.py` files as response schemas.
- **Prompt Inheritance**: Use `extends` to share model config (temperature, max_tokens) between templates.
- **Render State**: Remembers previous variables for precise partial updates via `.rerender()`.

### 3. Comparison with others
| Feature | DynaPrompt | Prompt-Poet / Promptix | f-strings |
| :--- | :---: | :---: | :---: |
| **Boilerplate** | Zero (just a folder) | Medium (manual registration) | High |
| **Lazy Loading** | ✅ Yes | ❌ No | ❌ No |
| **Env Layers** | ✅ Native | ⚠️ Manual | ❌ No |
| **Inheritance** | ✅ Native | ❌ No | ❌ No |
| **Schemas** | ✅ Auto-discovery | ⚠️ Manual | ❌ No |

---

## ✨ Features
- **File-based Prompt Management**: Write prompt templates in clean Markdown (`.md` or `.txt`) with YAML frontmatter, or group multiple prompts in a `prompts.toml` file.
- **Auto-Discovery & Companion Files**: Pass a directory like `settings_files=["prompts/"]` and DynaPrompt automatically loads all `.md` files. It also auto-discovers a sibling `prompts.toml` for managing metadata separately.
- **Automatic Name Sanitization**: Filenames like `Call Analysis.md` become `prompts.call_analysis`.
- **Validation & Hooks**: Enforce constraints on rendered prompts and intercept rendering with a powerful hook system.

## 🛠 Usage

### Loading from a Directory
DynaPrompt excels at organizing templates as files.

```python
from dynaprompt import DynaPrompt

prompts = DynaPrompt(
    settings_files=["examples/"], # Scans for .md, .toml, .py schemas
    environments=True
)

# Accessing analyzer.md template
rendered = prompts.analyzer.render(user_name="Emam", text="DynaPrompt is great!")

print(rendered.text)
print(rendered.config["model"]) # "gemini-1.5-pro" (from frontmatter or .toml)

# Partial update: keeps "user_name" but changes "text"
updated = prompts.analyzer.rerender(text="It's really fast.")
```

### Schema Integration
DynaPrompt automatically registers Pydantic models found in your `settings_files`.

```python
# If examples/schemas.py defines class UserProfile(BaseModel):
prompts = DynaPrompt(settings_files=["examples/"])

# Model is available as an attribute
user_schema = prompts.UserProfile

# Use it in rendering (automatically injects JSON schema if referenced in template)
rendered = prompts.fetch_user.render(username="em2m")
```

## 🔍 Inspection & Tab-Completion
DynaPrompt is designed for developer productivity.
- **Tab-Completion**: Use `dir(prompts)` or hit `Tab` in your IDE to see all available prompts and schemas.
- **History Tracking**: Inspect exactly where a prompt was loaded from and how it was merged across layers.

```python
# See loading history for a prompt
print(prompts.inspect("customer_support"))
```
