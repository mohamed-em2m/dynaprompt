from unittest.mock import patch

from dynaprompt import DynaPrompt


def test_skips_init_py_with_relative_import(tmp_path):
    """Test that __init__.py files are skipped even if they would error on load."""
    subdir = tmp_path / "prompts"
    subdir.mkdir()

    # Valid prompt file
    (subdir / "hello.md").write_text("Hello", encoding="utf-8")

    # __init__.py with relative import that would fail if executed in isolation
    (subdir / "__init__.py").write_text(
        "from ._prompts import PROMPTS", encoding="utf-8"
    )

    # This should not raise ImportError
    dp = DynaPrompt(settings_files=[str(subdir)])
    assert "hello" in dp.keys()


def test_infinite_loop_protection(tmp_path):
    """Test that the caller file is automatically excluded."""
    caller_file = (tmp_path / "my_app.py").resolve()
    caller_file.write_text("import dynaprompt", encoding="utf-8")

    # Mock FrameInfo
    class MockFrame:
        def __init__(self, filename):
            self.filename = filename

    # We need to mock inspect.stack()
    # It should return a list where at least one frame is NOT in dynaprompt
    mock_stack = [
        MockFrame("C:\\some\\path\\dynaprompt\\core.py"),
        MockFrame(str(caller_file)),
    ]

    with patch("inspect.stack", return_value=mock_stack):
        dp = DynaPrompt(settings_files=[str(tmp_path)])
        # Trigger setup
        dp.keys()
        assert caller_file in dp._wrapped._exclude_files


def test_introspection_methods(tmp_path):
    """Test keys(), __iter__ and .prompts property."""
    p = tmp_path / "p.toml"
    p.write_text(
        '[default.a]\ntemplate="A"\n[default.b]\ntemplate="B"\n', encoding="utf-8"
    )

    dp = DynaPrompt(settings_files=[str(p)])

    assert set(dp.keys()) == {"a", "b"}
    assert set(iter(dp)) == {"a", "b"}
    assert "a" in dp.prompts
    assert "b" in dp.prompts
    assert dp.prompts["a"].render().text == "A"
