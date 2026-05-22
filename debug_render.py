import pathlib
import shutil

from dynaprompt import DynaPrompt


def test_debug_render():
    prompts_dir = pathlib.Path("debug_prompts")
    prompts_dir.mkdir(exist_ok=True)

    with open(prompts_dir / "child.md", "w") as f:
        f.write("Child content")

    with open(prompts_dir / "parent.md", "w") as f:
        f.write("---\nvar: 'hello'\n---\nParent: {{var}}, {{child}}")

    try:
        dp = DynaPrompt(settings_files=[str(prompts_dir)], auto_render=True)

        print(f"Parent raw template: {dp.parent.raw_template!r}")
        print(f"Parent rendered text (auto): {dp.parent.text!r}")

        rendered = dp.parent.render()
        print(f"Parent rendered text (explicit): {rendered.text!r}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if prompts_dir.exists():
            shutil.rmtree(prompts_dir)


if __name__ == "__main__":
    test_debug_render()
