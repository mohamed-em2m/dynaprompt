# DynaPrompt Documentation

DynaPrompt is a powerful, lazy-loading prompt management and configuration library for LLM applications. Built on the core principles of **Dynaconf**, it provides a structured, enterprise-grade way to separate prompt logic from your application code.

## 🧠 Core Philosophy: Lazy Loading
Unlike many prompt libraries that load templates at import time, DynaPrompt is **lazy by design**.
- **Zero I/O at Start**: Creating a `DynaPrompt` object does not read any files.
- **On-Demand Resolution**: Files are only read, parsed, and merged the first time you access a prompt.
- **Environment Aware**: Seamlessly switch between `development`, `staging`, and `production` prompts without reloading your app.

---

## 🛠 Getting Started

### 1. Initialization
The `DynaPrompt` object is your main entry point. It handles discovery and registry.

```python
from dynaprompt import DynaPrompt

# Scans directories recursively for .md, .toml, .py, .json
prompts = DynaPrompt(settings_files=["prompts/", "config/vars.json"])
```

### 2. Flexible Storage
DynaPrompt supports multiple formats to suit different workflows:

- **Markdown (`.md` / `.txt`)**: Ideal for complex templates. Use YAML frontmatter for metadata (model, temperature, etc.).
- **TOML (`.toml`)**: Best for grouping multiple small prompts or defining environment-specific overrides.
- **Python (`.py`)**: Define schemas (Pydantic) or plain variables.
- **JSON/YAML**: For structured data and shared variables.

### 3. Recursive Directory Scanning
When you point DynaPrompt to a directory, it recursively scans for all supported files and builds a nested namespace reflecting the folder structure.

```bash
prompts/
  ├── auth/
  │   └── login.md
  └── support/
      └── chat.toml
```
Access them as: `prompts.auth.login` or `prompts.support.chat`.

---

## 🚀 Key Features

### 📤 Auto-Exporting (pyprompts.toml)
DynaPrompt can automatically generate a central configuration file representing your entire loaded structure. This is perfect for allowing non-technical users to override templates without touching the code.

```python
prompts = DynaPrompt(settings_files=["prompts/"], auto_export=True)
```

### 📦 Automatic Schema Integration
Register Pydantic models automatically from `.py` files. These can then be used for response validation or injected directly into templates as JSON schemas.

```python
# Referenced in prompt.md frontmatter:
# response_schema: UserProfile
rendered = prompts.my_prompt.render(user_id=123)
print(rendered.response_schema) # The UserProfile class
```

### 🪝 Powerful Hooks & Validation
Intercept the rendering process at any point:
- **Redact** PII before rendering.
- **Validate** that the output doesn't exceed a token limit.
- **Log** specific rendering events for audit trails.

---

## 🎨 Advanced Rendering
DynaPrompt supports a fluent API for quick overrides:

```python
prompt = prompts.chat_bot \
    .with_model("gpt-4o") \
    .with_temperature(0.7) \
    .render(user_message="Hello!")
```

It also supports **partial rerendering**, where it remembers previous variables:
```python
p1 = prompts.translate.render(text="Hello", lang="ES")
# Only update the text, 'lang' is preserved from p1
p2 = prompts.translate.rerender(text="Goodbye")
```
