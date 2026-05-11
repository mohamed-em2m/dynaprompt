from dynaprompt import DynaPrompt


def test_template_property_returns_raw_even_with_auto_render(tmp_path):
    """
    Ensures that .template returns the raw string with Jinja2 tags,
    even if auto_render=True has processed .text.
    """
    prompt_file = tmp_path / "test.md"
    prompt_file.write_text("---\nvar: 123\n---\nHello {{ name }}", encoding="utf-8")

    # auto_render=True is the default in DynaPrompt if not specified
    # and variables are provided.
    dp = DynaPrompt(
        settings_files=[str(prompt_file)],
        variables=[{"name": "World"}],
        auto_render=True,
    )

    node = dp.test

    # .text should be rendered
    assert node.text == "Hello World"

    # .template should still have the tag
    assert node.template == "Hello {{ name }}"

    # Setting template should update both
    node.template = "Hi {{ user }}"
    assert node.template == "Hi {{ user }}"


def test_template_manual_set_re_renders(tmp_path):
    """Ensures that manually setting .template triggers auto-render if enabled."""
    DynaPrompt(settings_files=[], variables=[{"user": "Ahmed"}], auto_render=True)
    from dynaprompt.nodes import PromptNode

    node = PromptNode(
        name="test", text="old", auto_render=True, variables={"user": "Ahmed"}
    )

    node.template = "Welcome {{ user }}"
    assert node.template == "Welcome {{ user }}"
    assert node.text == "Welcome Ahmed"
