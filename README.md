<p align="center"><img src="/art/dyna-prompt.png" alt="dyna-prompt logo"></p>

> **dyna-prompt** - Lazy-loading prompt configuration manager built directly on Dynaconf's principles.

[![MIT License](https://img.shields.io/badge/license-MIT-007EC7.svg?style=flat-square)](/LICENSE) [![PyPI](https://img.shields.io/pypi/v/dyna-prompt.svg)](https://pypi.python.org/pypi/dyna-prompt) [![Code Style Black](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

DynaPrompt is a powerful, lazy-loading prompt configuration manager inspired by Dynaconf. It offers a structured way to manage, version, and render LLM prompts while separating prompt text from configuration metadata.

## Install

```bash
pip install dyna-prompt
```

## Features
- **File-based Prompt Management**: Write prompt templates in clean Markdown (`.md` or `.txt`) with YAML frontmatter, or group multiple prompts in a `prompts.toml` file.
- **Auto-Discovery & Companion Files**: Pass a directory like `settings_files=["prompts/"]` and DynaPrompt automatically loads all `.md` files in it. It will also auto-discover a sibling `prompts.toml` companion file allowing you to manage metadata (like `model`, `temperature`, `max_tokens`) separately from your templates.
- **Automatic Name Sanitization**: Filenames like `Call Analysis.md` are automatically normalized into clean, snake-case identifiers (e.g. `prompts.call_analysis`).
- **Prefix Filtering**: Use `file_prefix="gpt_"` to only load files starting with a prefix, stripping it for a clean API (e.g., `prompts.support` instead of `gpt_support`).
- **Lazy Loading**: Zero I/O at instantiation. Files are only loaded when you access a prompt for the first time.
- **Environment Layering**: Render prompts differently per environment (`development`, `production`, etc.) without duplicating templates.
- **Validation & Hooks**: Enforce constraints on rendered prompts and intercept rendering using powerful hook systems.
- **Variable Tracking**: Automatically persists passed variables during `.render()`, enabling precise partial updates via `.rerender()`.

## Usage
```python
from dynaprompt import DynaPrompt

prompts = DynaPrompt(
    settings_files=["prompts/"], # Can be a directory of .md files or .toml files
    environments=True
)

# Rendering a template (e.g., loaded from prompts/customer_support.md)
rendered = prompts.customer_support.render(user_name="Ahmed", issue="Payment failed")

print(rendered.text)
print(rendered.config["model"])

# Partially re-render keeping the previous variables
updated_rendered = prompts.customer_support.rerender(user_name="Mohamed")
```

## Schema Auto-loading
DynaPrompt can automatically detect and register schemas from Python files or JSON files included in your `settings_files`.

- **Python Files**: All classes defined in `.py` files are registered. This is perfect for **Pydantic** models.
- **JSON Files**: Entire JSON objects are registered under their filename stem.

```python
# Pass a directory containing prompts.toml and schemas.py
prompts = DynaPrompt(settings_files=["prompts/"])

# Access auto-loaded Pydantic models directly as attributes
schema = prompts.AnalysisSchema
```

## Attribute Access & Tab-Completion
All loaded **prompts** and **schemas** are available as direct attributes of the `DynaPrompt` instance. 

- **Tab-Completion**: Use `dir(prompts)` or hit `Tab` in your IDE/IPython to see all available prompts and schemas.
- **Unified API**: No need to distinguish between where a schema or prompt came from—if it's in your settings folder, it's an attribute.

```python
# Access a prompt
rendered = prompts.customer_support.render(...)

# Access a schema (loaded from schemas.py or schema.json)
schema = prompts.UserProfile
```
