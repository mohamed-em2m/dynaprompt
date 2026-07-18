"""Tests for circular-reference / recursion protection in prompt rendering."""

from __future__ import annotations

import pathlib

import pytest

from dynaprompt import DynaPrompt


@pytest.fixture()
def recursion_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Two mutually-recursive prompts: prompt_a <-> prompt_b."""
    # prompt_a references prompt_b
    (tmp_path / "prompt_a.md").write_text(
        "A start -> {{prompts['prompt_b'].render().text}} -> A end"
    )
    # prompt_b references prompt_a
    (tmp_path / "prompt_b.md").write_text(
        "B start -> {{prompts['prompt_a'].render().text}} -> B end"
    )
    return tmp_path


@pytest.fixture()
def deep_recursion_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Three-level cycle: cycle_a -> cycle_b -> cycle_c -> cycle_a."""
    (tmp_path / "cycle_a.md").write_text("{{prompts['cycle_b'].render().text}}")
    (tmp_path / "cycle_b.md").write_text("{{prompts['cycle_c'].render().text}}")
    (tmp_path / "cycle_c.md").write_text("{{prompts['cycle_a'].render().text}}")
    return tmp_path


class TestRecursionProtection:
    def test_mutual_recursion_does_not_raise(self, recursion_dir: pathlib.Path):
        """A <-> B cycle must NOT raise RecursionError; handled gracefully."""
        dp = DynaPrompt(settings_files=[str(recursion_dir)])
        # Should complete without raising any error
        result = dp.prompt_a.render()
        assert result is not None

    def test_mutual_recursion_sentinel_in_output(self, recursion_dir: pathlib.Path):
        """The recursive back-reference is replaced with the sentinel string."""
        dp = DynaPrompt(settings_files=[str(recursion_dir)])
        result = dp.prompt_a.render()
        # The cycle is broken on one side; sentinel must appear somewhere
        assert "[Recursive reference to" in result.text

    def test_deep_cycle_does_not_raise(self, deep_recursion_dir: pathlib.Path):
        """Three-level A->B->C->A cycle is handled without RecursionError."""
        dp = DynaPrompt(settings_files=[str(deep_recursion_dir)])
        result = dp.cycle_a.render()
        assert result is not None
        assert "[Recursive reference to" in result.text

    def test_non_recursive_prompt_unaffected(self, tmp_path: pathlib.Path):
        """A prompt with no self-references renders normally."""
        (tmp_path / "hello.md").write_text("Hello, world!")
        dp = DynaPrompt(settings_files=[str(tmp_path)])
        result = dp.hello.render()
        assert result.text == "Hello, world!"
        assert "[Recursive reference to" not in result.text

    def test_self_reference_handled(self, tmp_path: pathlib.Path):
        """A prompt that references itself is caught by the render stack."""
        (tmp_path / "self_ref.md").write_text(
            "start -> {{prompts['self_ref'].render().text}} -> end"
        )
        dp = DynaPrompt(settings_files=[str(tmp_path)])
        result = dp.self_ref.render()
        assert result is not None
        assert "[Recursive reference to" in result.text
