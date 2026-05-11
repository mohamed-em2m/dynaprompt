# Changelog

All notable changes to this project will be documented here.

---

## [0.3.5] — 2026-05-11

### :bug: Fixed
- **Python Variable Stability**: Fixed a crash (`TypeError: cannot pickle 'module' object`) when loading Python files that contain standard imports (e.g. `import math`). Modules are now automatically excluded from the variable registry.

---

## [0.3.4] — 2026-05-11

### :sparkles: Added
- **`template` Property Alias**: `PromptNode` now supports `.template` as a more intuitive alias for the raw `.text` attribute.

### :bug: Fixed
- **Auto-Render Locking**: Fixed a regression where enabling `auto_render` would "lock" the template and prevent subsequent overrides in `.render()` calls.

---

## [0.3.3] — 2026-05-11

### :bug: Fixed

- **Infinite Loop Protection**: Automatically detects and excludes the caller script from the scanning process, preventing infinite recursion when using `.` as a settings directory.
- **Python Module Loading**: Directory scanning now automatically skips `__init__.py` files to avoid relative import errors in package-style prompt directories.

### :sparkles: Added

- **Introspection Methods**: `keys()`, `__iter__`, and `.prompts` property on `DynaPrompt` for easier exploration of loaded prompts.

---

## [0.3.0] — 2026-05-10

### :sparkles: Added

- **Async Rendering**: `async_render()` and `async_rerender()` on `PromptNode` for non-blocking I/O in FastAPI and async agents.
- **Async Hooks**: `@async_hookable` decorator for asynchronous lifecycle hooks.
- **Prompt Hashing**: Every `RenderedPrompt` now includes a `prompt_hash` (SHA-256) for audit logs and LangSmith observability.
- **Debug Trace**: `prompts.debug_trace("key")` to visualize the full merge hierarchy and identify which environment/file provided specific values.
- **Python Variable Templates**: Templates can be extracted from Python files using the `template = "file.py:variable"` syntax.

### :bug: Fixed

- **Dotted TOML Headers**: Nested TOML headers like `[default.gemini.analyzer]` were parsed as nested dicts instead of flat prompt namespaces.
- **Missing File Alerts**: Explicit `UserWarning` when a requested settings file doesn't exist.

### :pencil: Changed

- **README Overhaul**: Completely redesigned with side-by-side "before/after" comparisons, YAML frontmatter guides, and advanced examples.
- **Jinja2 Environment**: Enabled `enable_async=True` globally for transparent sync/async rendering.

---

## [0.2.0] — 2026-05-08

### :sparkles: Added

- **`structure_mode` Parameter**: Enables building nested namespaces from directory structures (e.g., `prompts.folder.file`). Defaults to `True`.
- **`auto_export` Visibility**: Improved documentation for the `auto_export` feature which mirrors the prompt tree to `pyprompts.toml`.
- **Enhanced Metadata**: Expanded PyPI keywords and Trove classifiers for better discoverability.

### :pencil: Changed

- **`auto_render` Default**: Now `True` by default. Variables within templates are automatically rendered during initialization.
- **Modernized Test Suite**: Refactored legacy test scripts into a clean `pytest` suite using `tmp_path` fixtures.

### :bug: Fixed

- **CI Workflow**: Fixed an "Invalid action input" error in GitHub Actions by updating Codecov to v5.

---

## [0.1.3] — 2026-05-04

- :tada: Initial public release with lazy-loading, environment support, and Pydantic schema integration.
