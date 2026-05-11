# Changelog

All notable changes to this project will be documented in this file.

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
