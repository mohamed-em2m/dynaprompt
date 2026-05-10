<p align="center"><img src="https://raw.githubusercontent.com/mohamed-em2m/dynaprompt/main/art/dynaprompt.png" alt="dynaprompt logo"></p>

> **dynaprompt** - Dynamic prompt management and configuration library for LLM applications. Powerful, lazy-loading, and supports Jinja2 templates and Pydantic schemas.

[![MIT License](https://img.shields.io/badge/license-MIT-007EC7.svg?style=flat-square)](https://github.com/mohamed-em2m/dynaprompt/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/dynaprompt.svg)](https://pypi.org/pypi/dynaprompt)
[![Code Style Black](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Coverage](https://img.shields.io/badge/coverage-75%25-green.svg)](https://github.com/mohamed-em2m/dynaprompt/tree/main/tests)

DynaPrompt is a powerful, lazy-loading prompt configuration manager inspired by **Dynaconf**. It offers a structured way to manage, version, and render LLM prompts while keeping your templates separate from your application logic.

---

<p align="center">
  <a href="#✨-features">Features</a> •
  <a href="#💡-why-dynaprompt">Why DynaPrompt?</a> •
  <a href="#🛠-usage">Usage</a> •
  <a href="#🔍-inspection">Inspection</a>
</p>

---

## 🚀 30-Second Quickstart

```bash
# Using pip
pip install dynaprompt

# Using uv (recommended)
uv add dynaprompt
```

1. **Create a `prompts.toml`** (or a directory of `.md` files):
```toml
[default.greeting]
template = "Hello {{ name }}! You are a helpful assistant."
model = "gpt-3.5-turbo"

[production.greeting]
template = "Hello {{ name }}! You are a professional consultant."
model = "gpt-4o"
```

2. **Use it in Python**:
```python
from dynaprompt import DynaPrompt

# 1. Initialize (zero I/O happens here)
prompts = DynaPrompt(settings_files=["prompts.toml"])

# 2. Render default environment
rendered = prompts.greeting.render(name="Emam")
print(rendered.text)
# -> "Hello Emam! You are a helpful assistant."

# 3. Switch environments seamlessly
with prompts.using_env("production"):
    prod_rendered = prompts.greeting.render(name="Emam")
    print(prod_rendered.text)
    # -> "Hello Emam! You are a professional consultant."
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

- **📂 File-based Management**: Write templates in clean Markdown (`.md`) with YAML frontmatter or group multiple prompts in a `prompts.toml`.
- **🏗️ Recursive Auto-Discovery**: Pass a directory like `settings_files=["prompts/"]` and DynaPrompt builds a nested namespace reflecting your folder structure.
- **⚡ Lazy Loading**: Zero I/O at import. Files are only read when a prompt is actually accessed.
- **🌍 Environment Layering**: Native support for `development`, `production`, etc. Override metadata per environment without touching the template.
- **🔧 Schema Auto-discovery**: Automatically registers **Pydantic** models, TypedDicts, and JSON schemas from your settings directories.
- **🧩 Jinja2 First-Class**: Supports recursive variable flattening, auto-rendering, and complex logic inside templates.
- **📤 Auto-Export**: Mirror your entire prompt structure to a central TOML file for easy external overrides.
- **🛡️ Validation & Hooks**: Enforce constraints on rendered output and intercept rendering with a powerful hook system.

## 🛠 Usage

### Loading from a Directory & Namespaces
DynaPrompt excels at organizing templates as files. When you load files from a nested directory structure (e.g., `examples/google/gemini.md`), it automatically builds a nested namespace.

```python
from dynaprompt import DynaPrompt

prompts = DynaPrompt(
    settings_files=["examples/"], # Scans for .md, .toml, .py schemas recursively
    environments=True
)

# Accessing a nested prompt using intuitive dot notation:
rendered = prompts.google.gemini.render(user_name="Emam", text="DynaPrompt is great!")

print(rendered.text)
print(rendered.config["model"]) # "gemini-1.5-pro" (from frontmatter or .toml)

# Partial update: keeps "user_name" but changes "text"
updated = prompts.google.gemini.rerender(text="It's really fast.")
```

### Auto-Exporting Prompts to TOML
You can automatically export your entire loaded prompt structure into a central `pyprompts.toml` file. To keep things clean and optimized:
- **Multiline Templates**: Saved as separate `.md` files in a `prompts/` directory.
- **TOML**: References these files by relative path.

This makes your configuration much more readable and easier to manage in version control.

```python
# Pass auto_export=True, or auto_export="custom_path.toml"
prompts = DynaPrompt(settings_files=["examples/"], auto_export=True)

# Access a prompt to trigger the lazy load and export
_ = prompts.google.gemini
```

### File-Based Templates and Variables
DynaPrompt is designed to keep your configuration files clean. Instead of long strings, you can reference external files and modules directly.

#### 1. Templates by Path
In your TOML config, if a `template` value is a single-line string that resolves to a file, DynaPrompt reads it automatically.
```toml
[default.my_prompt]
template = "prompts/my_template.md"  # Transparently loaded
```

#### 2. Flexible Variables
The `variables` field (both globally and per-prompt) supports dynamic resolution from files and modules:
```toml
[default.my_prompt]
# Multiple formats supported:
variables = [
    "config/vars.json",           # File path
    "config/settings.py:vars",    # Extract 'vars' attribute from a .py file
    "myapp.config.defaults",      # Dotted module path
    "myapp.config:constants"      # Dotted module + explicit attribute
]
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
