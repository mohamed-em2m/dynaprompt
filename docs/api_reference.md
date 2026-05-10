# DynaPrompt API Reference

## DynaPrompt

The main lazy-loading settings manager.

### `__init__`
- `settings_files`: (list) List of files or directories to load.
- `environments`: (bool) Enable environment support. Default `True`.
- `env`: (str) Initial environment. Defaults to `ENV_FOR_DYNAPROMPT` or `"development"`.
- `validators`: (list) List of `PromptValidator` instances.
- `file_prefix`: (str) Optional prefix to filter files (e.g. `gpt_`).
- `variables`: (list) List of paths or direct dictionaries to load into the global context. Supports flexible formats:
    - File paths: `"config/vars.json"`, `"config/settings.py:my_vars"` (with attribute extraction).
    - Dotted modules: `"myapp.config"`, `"myapp.config.constants"`.
- `auto_render`: (bool) If `True`, renders nested variables within templates during initialization. Default `True`.
- `auto_export`: (bool|str) If `True` (or a path), automatically exports the loaded prompt structure to a TOML file on first access. Multiline templates are saved as separate files in a `prompts/` directory to keep the TOML clean.
- `structure_mode`: (bool) If `True`, builds nested namespaces from directory structure. Default `True`.

### Attribute Access
Access prompts and schemas directly:
- `prompts.my_prompt`: Returns a `PromptNode`.
- `prompts.MySchema`: Returns a registered schema (Pydantic model, JSON, etc).
- `prompts.namespace.sub_prompt`: Access nested prompts using dot notation.

### Methods
- `get(name)`: Explicit getter for prompts or schemas.
- `using_env(env)`: Context manager for temporary environment switching.
- `inspect(name=None)`: Returns loading history and merge details for debugging.
- `reload()`: Discards cache and reloads all files from disk.
- `export_to_toml(filepath)`: Manually export the current prompt configuration to TOML.
- `add_validator(*validators)`: Register new validators globally.
- `add_hook(event, name_or_hook, hook=None)`: Register a hook for `before_render` or `after_render`.

## PromptNode

The object representing a single loaded prompt.

### Methods
- `render(**kwargs)`: Renders the template using Jinja2 and returns a `RenderedPrompt`. Supports keyword arguments or a single positional dictionary.
- `rerender(**kwargs)`: Renders again using previously used variables as a base.
- `with_model(model_name)`: Returns a new `PromptNode` with the model overridden.
- `with_temperature(value)`: Returns a new `PromptNode` with temperature overridden.
- `with_max_tokens(value)`: Returns a new `PromptNode` with max_tokens overridden.
- `with_schema(schema)`: Returns a new `PromptNode` with the response schema overridden.

## RenderedPrompt

The result of calling `.render()`.

### Attributes
- `text`: The final rendered prompt string.
- `config`: A dictionary of all metadata (model, temperature, etc).
- `response_schema`: The resolved schema class/data.
- `current_env`: The environment used for this render.
