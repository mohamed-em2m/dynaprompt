from __future__ import annotations

import pathlib
from typing import Any


class FileResolver:
    """Handles file discovery and path resolution for prompts and schemas."""

    def __init__(self, file_prefix: str | None = None, structure_mode: bool = True):
        self.file_prefix = file_prefix
        self.structure_mode = structure_mode

    def resolve_all(self, settings_files: list[Any]) -> list[pathlib.Path | dict]:
        """Convert input list into absolute paths and explicit file markers."""
        resolved: list[pathlib.Path | dict] = []
        explicit_files: set[pathlib.Path] = set()

        # Pass 1: Resolution
        for item in settings_files:
            if isinstance(item, dict):
                resolved.append(item)
                continue

            path = pathlib.Path(item).resolve()
            resolved.append(path)
            if not path.is_dir():
                explicit_files.add(path)

        return resolved, explicit_files

    def scan_directory(
        self, directory: pathlib.Path, supported_suffixes: tuple[str, ...]
    ) -> list[tuple[pathlib.Path, str]]:
        """Scan directory and return list of (path, sanitized_name)."""
        results: list[tuple[pathlib.Path, str]] = []
        seen_names: dict[str, pathlib.Path] = {}

        for child in sorted(directory.rglob("*")):
            if not child.is_file() or child.name == "__init__.py":
                continue
            if child.suffix not in supported_suffixes:
                continue

            rel_path = child.relative_to(directory)
            if self.structure_mode:
                parts = rel_path.with_suffix("").parts
            else:
                parts = (child.stem,)

            stem = ".".join(parts)

            if self.file_prefix:
                if not stem.startswith(self.file_prefix):
                    continue
                stem = stem[len(self.file_prefix) :]

            from ..utils import sanitize_name

            sanitized = ".".join(sanitize_name(part) for part in parts)

            if sanitized in seen_names:
                i = 2
                candidate = f"{sanitized}_{i}"
                while candidate in seen_names:
                    i += 1
                    candidate = f"{sanitized}_{i}"
                sanitized = candidate

            seen_names[sanitized] = child
            results.append((child, sanitized))

        return results
