"""
Tests for core DynaPrompt loading, rendering, and environment switching.
"""

from __future__ import annotations

import pytest

from dynaprompt import DynaPrompt
from dynaprompt.nodes import PromptNode, RenderedPrompt

# ──────────────────────────────────────────────────────────────────────────────
# Basic loading
# ──────────────────────────────────────────────────────────────────────────────


class TestMarkdownLoading:
    def test_loads_md_prompt(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        dp.inspect()
        assert "greet" in dp._wrapped._store

    def test_md_prompt_returns_node(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        node = dp.greet
        assert isinstance(node, PromptNode)

    def test_md_prompt_renders(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.render(name="Ahmed", app="TestApp")
        assert isinstance(rendered, RenderedPrompt)
        assert "Ahmed" in rendered.text
        assert "TestApp" in rendered.text

    def test_md_prompt_config(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.render(name="x", app="y")
        assert rendered.config["model"] == "gpt-4o"
        assert rendered.config["temperature"] == 0.5

    def test_rendered_str(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.render(name="Ali", app="Z")
        assert str(rendered) == rendered.text


class TestTomlLoading:
    def test_loads_toml_prompt(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)])
        dp.inspect()
        assert "support" in dp._wrapped._store

    def test_toml_renders(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)])
        rendered = dp.support.render(user="Emam", issue="login failed")
        assert "Emam" in rendered.text
        assert "login failed" in rendered.text

    def test_toml_default_model(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)])
        rendered = dp.support.render(user="x", issue="y")
        assert rendered.config["model"] == "gpt-3.5"

    def test_toml_dotted_keys_flattening(self, tmp_path):
        """Test that [default.a.b] is flattened to prompt name 'a.b'."""
        p = tmp_path / "dotted.toml"
        p.write_text('[default.gemini.analyzer]\nmodel = "gpt-4"\n', encoding="utf-8")
        dp = DynaPrompt(settings_files=[str(p)])
        dp.inspect()
        assert "gemini.analyzer" in dp._wrapped._store
        assert dp.gemini.analyzer.metadata["model"] == "gpt-4"

    def test_toml_template_path_resolution(self, tmp_path):
        """Test that 'template = path' automatically reads the file."""
        template_path = tmp_path / "hello.md"
        template_path.write_text("Hello {{ name }}", encoding="utf-8")

        toml_path = tmp_path / "prompts.toml"
        toml_path.write_text(
            f'[default.greet]\ntemplate = "{template_path.name}"\n', encoding="utf-8"
        )

        # Load from tmp_path where both files reside
        dp = DynaPrompt(settings_files=[str(toml_path)])
        rendered = dp.greet.render(name="Path")
        assert "Hello Path" in rendered.text

    def test_toml_template_python_resolution(self, tmp_path):
        """Test that 'template = file.py:variable' extracts the python variable."""
        py_path = tmp_path / "my_prompts.py"
        py_path.write_text(
            'my_string = "Hello {{ name }} from Python!"', encoding="utf-8"
        )

        toml_path = tmp_path / "prompts.toml"
        toml_path.write_text(
            f'[default.greet]\ntemplate = "./{py_path.name}:my_string"\n',
            encoding="utf-8",
        )

        dp = DynaPrompt(settings_files=[str(toml_path)])
        rendered = dp.greet.render(name="World")
        assert rendered.text == "Hello World from Python!"


class TestDirectoryLoading:
    def test_loads_from_directory(self, prompts_dir):
        dp = DynaPrompt(settings_files=[str(prompts_dir)])
        dp.inspect()
        assert "greet" in dp._wrapped._store

    def test_missing_file_is_silent(self, tmp_path):
        """Missing files should not raise — they are silently skipped."""
        dp = DynaPrompt(settings_files=[str(tmp_path / "nonexistent.toml")])
        dp.inspect()
        assert dp._wrapped._store == {}


# ──────────────────────────────────────────────────────────────────────────────
# Environment layering
# ──────────────────────────────────────────────────────────────────────────────


class TestEnvironments:
    def test_default_env(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)], env="development")
        rendered = dp.support.render(user="x", issue="y")
        assert rendered.config["model"] == "gpt-3.5"

    def test_production_env_override(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)], env="production")
        rendered = dp.support.render(user="x", issue="y")
        assert rendered.config["model"] == "gpt-4o"

    def test_using_env_context_manager(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)], env="development")
        dp.inspect()  # trigger load

        assert dp.support.render(user="x", issue="y").config["model"] == "gpt-3.5"

        with dp.using_env("production"):
            assert dp.support.render(user="x", issue="y").config["model"] == "gpt-4o"

        # Should revert after context exits
        assert dp.support.render(user="x", issue="y").config["model"] == "gpt-3.5"

    def test_current_env_property(self, toml_prompts):
        dp = DynaPrompt(settings_files=[str(toml_prompts)], env="development")
        assert dp.current_env == "development"


# ──────────────────────────────────────────────────────────────────────────────
# Attribute access and __dir__
# ──────────────────────────────────────────────────────────────────────────────


class TestAttributeAccess:
    def test_getattr_prompt(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        assert isinstance(dp.greet, PromptNode)

    def test_getattr_missing_raises(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        dp.inspect()
        with pytest.raises(AttributeError, match="nonexistent"):
            _ = dp.nonexistent

    def test_dir_includes_prompts(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        dp.inspect()
        assert "greet" in dir(dp)

    def test_dir_includes_schemas(self, py_schemas):
        dp = DynaPrompt(settings_files=[str(py_schemas)])
        dp.inspect()
        assert "UserSchema" in dir(dp)
        assert "ResponseSchema" in dir(dp)

    def test_schema_accessible_as_attribute(self, py_schemas):
        dp = DynaPrompt(settings_files=[str(py_schemas)])
        dp.inspect()
        cls = dp.UserSchema
        assert cls.__name__ == "UserSchema"

    def test_get_method(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        node = dp.get("greet")
        assert isinstance(node, PromptNode)


# ──────────────────────────────────────────────────────────────────────────────
# Fluent API on PromptNode
# ──────────────────────────────────────────────────────────────────────────────


class TestPromptNodeFluentAPI:
    def test_with_model(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.with_model("claude-opus").render(name="x", app="y")
        assert rendered.config["model"] == "claude-opus"

    def test_with_temperature(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.with_temperature(0.1).render(name="x", app="y")
        assert rendered.config["temperature"] == 0.1

    def test_with_max_tokens(self, md_prompt):
        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.with_max_tokens(100).render(name="x", app="y")
        assert rendered.config["max_tokens"] == 100

    def test_with_schema(self, md_prompt):
        from pydantic import BaseModel

        class MyModel(BaseModel):
            result: str

        dp = DynaPrompt(settings_files=[str(md_prompt)])
        rendered = dp.greet.with_schema(MyModel).render(name="x", app="y")
        assert rendered.response_schema is MyModel
