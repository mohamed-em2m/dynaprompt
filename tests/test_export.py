from dynaprompt import DynaPrompt


def test_auto_export_to_toml(tmp_path):
    # Setup test prompts directory
    prompts_dir = tmp_path / "test_prompts"
    google_dir = prompts_dir / "google"
    google_dir.mkdir(parents=True)
    (google_dir / "gemini.md").write_text(
        "---\nmodel: test\n---\nHello {{ name }}!", encoding="utf-8"
    )

    export_file = tmp_path / "pyprompts.toml"

    # Initialize with auto_export pointing to tmp_path
    dp = DynaPrompt(settings_files=[str(prompts_dir)], auto_export=str(export_file))

    # Trigger lazy load
    _ = dp.google.gemini

    assert export_file.exists()
    content = export_file.read_text(encoding="utf-8")
    assert "[default.google.gemini]" in content
    assert 'model = "test"' in content
