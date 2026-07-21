# DynaPrompt: Automatic Schema Loading

One of the most powerful features of DynaPrompt is the ability to automatically discover and register your response schemas (Pydantic models, TypedDicts, or raw JSON).

## How it works

When you pass a list of files or a directory to `settings_files`, DynaPrompt scans for `.py` and `.json` files.

### 1. Python Schemas (.py)
Any Python class defined in a file within your settings path is automatically registered.

**Example (`schemas.py`):**
```python
from pydantic import BaseModel

class UserSchema(BaseModel):
    name: str
    age: int
```

**Usage:**
```python
prompts = DynaPrompt(settings_files=["schemas.py"])
# UserSchema is now available as prompts.UserSchema
```

### 2. JSON Schemas (.json)
If you have schemas defined as raw JSON (e.g., for simple structure matching or external tools), they are loaded and registered under their filename stem.

**Example (`response_format.json`):**
```json
{
  "status": "string",
  "data": "object"
}
```

**Usage:**
```python
prompts = DynaPrompt(settings_files=["response_format.json"])
# The JSON data is available as prompts.response_format
```

## Referencing Schemas in Prompts

Once a schema is registered (either automatically or via `register()`), you can reference it by its string name in your prompt frontmatter.

**Example (`prompt.md`):**
```markdown
---
model: gpt-4
response_schema: UserSchema
---
Extract user info from: {{ text }}
```

DynaPrompt will automatically resolve the string `"UserSchema"` to the actual class/data when the prompt is loaded.
