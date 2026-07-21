# Changelog

All notable changes to this project will be documented in this file.

## [0.5.0] - 2026-07-18

### Added
- **Automatic Cache Cleanup**: `DynaPrompt` now tracks every `__pycache__` directory
  that Python creates when loading external `.py` schema and variable files via
  `importlib`. These are removed automatically when `cleanup()` is called.
- **`.dynaprompt` Folder Cleanup**: Any `.dynaprompt` directory found inside a scanned
  settings root is removed during cleanup, preventing stale artefacts from accumulating
  across runs.
- **`cleanup()` Method**: Explicit cleanup API — call `prompts.cleanup()` at any point
  to remove all ephemeral cache directories created since the last load.
- **Context-Manager Support**: `DynaPrompt` now implements `__enter__` / `__exit__`,
  so cleanup runs automatically when used as a context manager:
  ```python
  with DynaPrompt(settings_files=["prompts/"]) as p:
      result = p.my_prompt.render()
  # __pycache__ and .dynaprompt dirs deleted here
  ```
- **`reload()` now cleans up first**: Calling `reload()` triggers `cleanup()` before
  resetting the internal state, ensuring no stale cache directories linger between
  reloads.

## [0.4.0] - 2026-05-22

### Added
- **Nested Prompt Support**: Prompts can now be included inside other prompts using the `{{prompt_name}}` syntax.
- **Recursion Protection**: Implemented a render stack to prevent circular references between prompts (e.g., A includes B, B includes A). Detected loops are replaced with a safe warning message instead of a `RecursionError`.
- **Enhanced Variable Registry**: The directory scanner now skips internal and hidden directories (like `.venv`, `.git`, `__pycache__`) by default to prevent self-loading or `ImportError`.

### Fixed
- **Synchronous Rendering Compatibility**: Fixed a bug where `enable_async=True` in Jinja2 was causing synchronous `render()` calls to return coroutines instead of text. Sync and Async rendering now utilize separate pre-compiled templates.
- **Auto-Render Lifecycle**: Refactored `auto_render` to use a "silent" internal render. This ensures variables and schemas are rendered during initialization without triggering lifecycle hooks twice.
- **Schema Context Injection**: Global schemas (from shared `.py` or `.json` files) are now automatically injected into all prompt contexts, including nested prompts.

## [0.3.6] - 2026-05-11

## [0.3.5] - 2026-05-11

### Fixed
- **Python Variable Stability**: Fixed a crash (`TypeError: cannot pickle 'module' object`) when loading Python files that contain standard imports (e.g. `import math`). Modules are now automatically excluded from the variable registry.

## [0.3.4] - 2026-05-11

### Added
- **`template` Property Alias**: `PromptNode` now supports `.template` as a more intuitive alias for the raw `.text` attribute.

### Fixed
- **Auto-Render Locking**: Fixed a regression where enabling `auto_render` would "lock" the template and prevent subsequent overrides in `.render()` calls.


## [0.3.3] - 2026-05-11

### Added
- **Introspection Methods**: Added `keys()`, `__iter__`, and a `.prompts` property to `DynaPrompt` for easier exploration of loaded prompts.

### Fixed
- **Infinite Loop Protection**: Added automatic detection and exclusion of the caller script from the scanning process. This prevents infinite recursion when passing `.` or the script's own path as a settings directory.
- **Python Module Loading**: Directory scanning now automatically skips `__init__.py` files to avoid relative import errors when loading Python-based schemas or variables.


## [0.3.0] - 2026-05-10

### Added
- **Async Support**: Introduced `async_render()` and `async_rerender()` for non-blocking I/O in FastAPI/Async applications.
- **Async Hooks**: Added `@async_hookable` decorator to support asynchronous lifecycle hooks.
- **Prompt Hashing**: Every `RenderedPrompt` now includes a `prompt_hash` for audit logs and LangSmith/LangChain observability.
- **Debug Trace**: New `prompts.debug_trace("key")` method to visualize the "merge" hierarchy and identify which environment/file provided specific values.
- **Python Variable Templates**: Templates can now be extracted directly from Python files using the `template = "file.py:variable"` syntax.

### Fixed
- **Dotted TOML Headers**: Fixed a bug where nested TOML headers (e.g., `[default.gemini.analyzer]`) were parsed as nested dictionaries instead of flat prompt namespaces.
- **Missing File Alerts**: Added explicit `UserWarning` when a requested settings file in `settings_files` does not exist on the filesystem.

### Changed
- **README Overhaul**: Completely redesigned the README with side-by-side comparisons ("Before/After"), YAML Frontmatter guides, and advanced examples for hooks/validators.
- **Jinja2 Environment**: Enabled `enable_async=True` globally in the Jinja2 environment to allow transparent support for both sync and async rendering.


## [0.2.0] - 2026-05-08

### Added
- **`structure_mode` Parameter**: New initialization parameter (defaults to `True`) that enables building nested namespaces from directory structures (e.g., `prompts.folder.file`).
- **`auto_export` Visibility**: Improved documentation for the `auto_export` feature which mirrors the prompt tree to `pyprompts.toml`.
- **Enhanced Metadata**: Expanded PyPI keywords and Trove classifiers for better discoverability.
- **Project URLs**: Added links for Documentation, Issue Tracker, and Changelog to the PyPI profile.

### Changed
- **`auto_render` Default**: Now defaults to `True`. Variables within templates will be automatically rendered during the initialization phase for better consistency.
- **Modernized Test Suite**: Refactored legacy test scripts into a clean `pytest` suite using `tmp_path` fixtures for isolation.
- **Root Directory Cleanup**: Removed all temporary and manual test files from the project root.

### Fixed
- **CI Workflow**: Fixed an "Invalid action input" error in the GitHub Actions workflow by updating the Codecov action to version 5 and using the correct `files` parameter.

### Documentation
- **API Reference**: Added a comprehensive `docs/api_reference.md`.
- **User Guide**: Updated `docs/dynaprompt.md` with detailed architecture and feature explanations.
- **README**: Redesigned with better formatting, icons, and `uv` installation instructions.

## [0.1.3] - 2026-05-04
- Initial release with lazy-loading, environment support, and Pydantic schema integration.
