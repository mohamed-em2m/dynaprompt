from dynaprompt import DynaPrompt


def test_external_template_and_variables(tmp_path):
    # 1. Test template as a path
    template_file = tmp_path / "test_external_template.md"
    template_file.write_text("Hello {{ external_var }}", encoding="utf-8")

    # 2. Test variables as a path
    vars_file = tmp_path / "test_vars.json"
    vars_file.write_text('{"external_var": "world from json"}', encoding="utf-8")

    # 3. Create a toml defining a prompt that uses both
    config_file = tmp_path / "test_config.toml"
    config_file.write_text(
        f"""
[default.my_external_prompt]
template = "{template_file.as_posix()}"
variables = "{vars_file.as_posix()}"

[default.my_dict_prompt]
template = "{template_file.as_posix()}"
[default.my_dict_prompt.variables]
external_var = "world from dict"
""",
        encoding="utf-8",
    )

    dp = DynaPrompt(settings_files=[str(config_file)])

    # Test 1: variables loaded from file path
    r1 = dp.my_external_prompt.render()
    assert r1.text == "Hello world from json"

    # Test 2: variables loaded from inline dict
    r2 = dp.my_dict_prompt.render()
    assert r2.text == "Hello world from dict"
