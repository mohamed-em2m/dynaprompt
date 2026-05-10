"""
Tests for the variables= parameter and _load_variables_file internals.
Covers: dicts, JSON, YAML, TOML, Python files, collision namespacing,
and auto-injection into render context.
"""

from __future__ import annotations

import pytest

from dynaprompt import DynaPrompt

# ──────────────────────────────────────────────────────────────────────────────
# Dict variables
# ──────────────────────────────────────────────────────────────────────────────


class TestDictVariables:
    def test_dict_keys_available(self, toml_prompts):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[{"app_name": "MyApp", "version": "2.0"}],
        )
        dp.inspect()
        assert dp._wrapped._variables["app_name"] == "MyApp"
        assert dp._wrapped._variables["version"] == "2.0"

    def test_dict_saved_under_container_key(self, toml_prompts):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[{"k": "v"}],
        )
        dp.inspect()
        # Container key is dict_0 for first dict
        assert "dict_0" in dp._wrapped._variables
        assert dp._wrapped._variables["dict_0"] == {"k": "v"}

    def test_multiple_dicts_indexed(self, toml_prompts):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[{"a": 1}, {"b": 2}],
        )
        dp.inspect()
        assert "dict_0" in dp._wrapped._variables
        assert "dict_1" in dp._wrapped._variables

    def test_dict_warns_on_merge(self, toml_prompts):
        with pytest.warns(UserWarning, match="Merging direct dictionary"):
            dp = DynaPrompt(
                settings_files=[str(toml_prompts)],
                variables=[{"x": 1}],
            )
            dp.inspect()


# ──────────────────────────────────────────────────────────────────────────────
# File-based variables
# ──────────────────────────────────────────────────────────────────────────────


class TestJsonVariables:
    def test_json_file_keys_available(self, toml_prompts, json_vars):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(json_vars)],
        )
        dp.inspect()
        assert dp._wrapped._variables["app"] == "DynaPrompt"
        assert dp._wrapped._variables["version"] == "1.0"

    def test_json_container_key(self, toml_prompts, json_vars):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(json_vars)],
        )
        dp.inspect()
        assert "vars" in dp._wrapped._variables  # stem of vars.json
        assert isinstance(dp._wrapped._variables["vars"], dict)

    def test_json_in_settings_files(self, json_vars):
        dp = DynaPrompt(settings_files=[str(json_vars)])
        dp.inspect()
        assert dp._wrapped._variables["app"] == "DynaPrompt"


class TestYamlVariables:
    def test_yaml_file_keys_available(self, toml_prompts, yaml_vars):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(yaml_vars)],
        )
        dp.inspect()
        assert dp._wrapped._variables["lang"] == "English"
        assert dp._wrapped._variables["author"] == "Emam"

    def test_yaml_container_key(self, toml_prompts, yaml_vars):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(yaml_vars)],
        )
        dp.inspect()
        assert "vars" in dp._wrapped._variables


class TestTomlVariables:
    def test_toml_file_keys_available(self, toml_prompts, toml_vars):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(toml_vars)],
        )
        dp.inspect()
        assert dp._wrapped._variables["env_name"] == "dev"
        assert dp._wrapped._variables["debug"] is True


class TestPythonFileVariables:
    def test_py_variables_loaded(self, toml_prompts, py_schemas):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(py_schemas)],
        )
        dp.inspect()
        assert dp._wrapped._variables["GREETING"] == "hello"
        assert dp._wrapped._variables["MAX_TOKENS"] == 512

    def test_py_classes_as_schemas_and_variables(self, toml_prompts, py_schemas):
        dp = DynaPrompt(
            settings_files=[str(toml_prompts)],
            variables=[str(py_schemas)],
        )
        dp.inspect()
        assert "UserSchema" in dp.schemas
        assert "UserSchema" in dp._wrapped._variables


# ──────────────────────────────────────────────────────────────────────────────
# Collision handling
# ──────────────────────────────────────────────────────────────────────────────


class TestCollisionHandling:
    def test_collision_namespaced(self, toml_prompts):
        with pytest.warns(UserWarning):
            dp = DynaPrompt(
                settings_files=[str(toml_prompts)],
                variables=[
                    {"status": "active"},
                    {"status": "pending"},  # collision
                ],
            )
            dp.inspect()

        vars_ = dp._wrapped._variables
        assert vars_["status"] == "active"  # first wins
        assert vars_["status_dict"] == "pending"  # second namespaced

    def test_collision_warning_message(self, toml_prompts):
        with pytest.warns(UserWarning, match="'status' already exists"):
            dp = DynaPrompt(
                settings_files=[str(toml_prompts)],
                variables=[{"status": "a"}, {"status": "b"}],
            )
            dp.inspect()

    def test_missing_file_warns(self, toml_prompts):
        with pytest.warns(UserWarning, match="Could not resolve"):
            dp = DynaPrompt(
                settings_files=[str(toml_prompts)],
                variables=["/nonexistent/path/vars.json"],
            )
            dp.inspect()


# ──────────────────────────────────────────────────────────────────────────────
# Auto-injection into render context
# ──────────────────────────────────────────────────────────────────────────────


class TestVariableInjectionIntoRender:
    def test_dict_var_injected(self, tmp_path):
        prompt = tmp_path / "hello.md"
        prompt.write_text(
            "---\nmodel: gpt-4\n---\nHello {{ app_name }}!", encoding="utf-8"
        )
        dp = DynaPrompt(
            settings_files=[str(prompt)],
            variables=[{"app_name": "DynaPrompt"}],
        )
        rendered = dp.hello.render()
        assert "DynaPrompt" in rendered.text

    def test_json_var_injected(self, tmp_path, json_vars):
        prompt = tmp_path / "info.md"
        prompt.write_text(
            "---\nmodel: gpt-4\n---\nVersion: {{ version }}", encoding="utf-8"
        )
        dp = DynaPrompt(
            settings_files=[str(prompt)],
            variables=[str(json_vars)],
        )
        rendered = dp.info.render()
        assert "1.0" in rendered.text

    def test_render_kwarg_overrides_injected_var(self, tmp_path):
        """Explicit render(name=...) should win over an injected variable."""
        prompt = tmp_path / "greet.md"
        prompt.write_text("---\nmodel: gpt-4\n---\nHi {{ name }}", encoding="utf-8")
        dp = DynaPrompt(
            settings_files=[str(prompt)],
            variables=[{"name": "FromVars"}],
        )
        rendered = dp.greet.render(name="FromKwarg")
        assert "FromKwarg" in rendered.text
        assert "FromVars" not in rendered.text


# ──────────────────────────────────────────────────────────────────────────────
# Auto-render (nested variables)
# ──────────────────────────────────────────────────────────────────────────────


class TestAutoRenderVariables:
    def test_variables_reference_each_other(self):
        variables = [
            {"base": "http://api.com"},
            {"auth": "{{ base }}/auth"},
            {"login": "{{ auth }}/login"},
        ]
        dp = DynaPrompt(
            settings_files=[],
            variables=variables,
            auto_render=True,
        )
        dp.inspect()
        vars_ = dp._wrapped._variables
        assert vars_["base"] == "http://api.com"
        assert vars_["auth"] == "http://api.com/auth"
        assert vars_["login"] == "http://api.com/auth/login"

    def test_auto_render_disabled_by_default(self):
        variables = [
            {"base": "http://api.com"},
            {"auth": "{{ base }}/auth"},
        ]
        dp = DynaPrompt(
            settings_files=[],
            variables=variables,
            auto_render=False,
        )
        dp.inspect()
        vars_ = dp._wrapped._variables
        assert vars_["auth"] == "{{ base }}/auth"
