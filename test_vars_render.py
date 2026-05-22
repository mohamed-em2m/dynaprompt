import pathlib

from dynaprompt import DynaPrompt


def test_auto_render_variables():
    # Create temporary prompt files
    prompts_dir = pathlib.Path("temp_prompts_vars")
    prompts_dir.mkdir(exist_ok=True)

    # Prompt with variables
    with open(prompts_dir / "agent.md", "w") as f:
        f.write("---\nvariables:\n  name: 'Agent X'\n---\nHello, my name is {{name}}.")

    try:
        # Initialize with auto_render=True
        dp = DynaPrompt(settings_files=[str(prompts_dir)], auto_render=True)

        # Access the prompt
        agent = dp.agent
        print(f"Agent text: {agent.text!r}")

        if "Agent X" not in agent.text:
            print("FAILURE: Variables not rendered in .text")
        else:
            print("SUCCESS: Variables rendered correctly in .text")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        import shutil

        if prompts_dir.exists():
            shutil.rmtree(prompts_dir)


if __name__ == "__main__":
    test_auto_render_variables()
