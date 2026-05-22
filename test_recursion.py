import pathlib
import shutil

from dynaprompt import DynaPrompt


def test_recursion():
    prompts_dir = pathlib.Path("recursion_test")
    prompts_dir.mkdir(exist_ok=True)

    # Create circular dependency
    # Prompt A includes Prompt B
    with open(prompts_dir / "A.md", "w") as f:
        f.write("A start -> {{B}} -> A end")

    # Prompt B includes Prompt A
    with open(prompts_dir / "B.md", "w") as f:
        f.write("B start -> {{A}} -> B end")

    try:
        # Note: auto_render=True would normally trigger recursion on startup
        # But our new LazyContext and render() check should handle it.
        dp = DynaPrompt(settings_files=[str(prompts_dir)], auto_render=True)

        print("Rendering A...")
        rendered = dp.A.render()
        print(f"Result A:\n{rendered.text}")

        assert "[Recursive reference to 'A' detected]" in rendered.text
        print("SUCCESS: Recursion detected and handled gracefully!")

    except RecursionError:
        print("FAILURE: Got RecursionError!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if prompts_dir.exists():
            shutil.rmtree(prompts_dir)


if __name__ == "__main__":
    test_recursion()
