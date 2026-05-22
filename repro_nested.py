import pathlib
import shutil
import traceback

from dynaprompt import DynaPrompt


def test_nested_prompts():
    # Create temporary prompt files
    prompts_dir = pathlib.Path("temp_prompts")
    prompts_dir.mkdir(exist_ok=True)

    tools_content = "tool1, tool2"
    with open(prompts_dir / "tools.md", "w") as f:
        f.write(tools_content)

    agent_content = """---
model: gpt-4
---
you are intlegente agent
you can use this tools
{{tools}}
"""
    with open(prompts_dir / "agent.md", "w") as f:
        f.write(agent_content)

    try:
        dp = DynaPrompt(settings_files=[str(prompts_dir)])

        # Test 1: Direct access
        print("Testing direct access...")
        rendered = dp.agent.render()
        print(f"Rendered text:\n{rendered.text}")
        if tools_content in rendered.text:
            print("SUCCESS: Nested prompt 'tools' rendered inside 'agent'!")
        else:
            print("FAILURE: Nested prompt NOT rendered correctly.")
            print(f"Actual output: {rendered.text!r}")

        # Test 2: Explicit 'prompts' accessor
        print("\nTesting explicit 'prompts' accessor...")
        agent_explicit_content = """{{prompts.tools}}"""
        dp.agent.template = agent_explicit_content
        rendered_explicit = dp.agent.render()
        if tools_content in rendered_explicit.text:
            print("SUCCESS: Explicit 'prompts.tools' rendered!")
        else:
            print("FAILURE: Explicit 'prompts.tools' NOT rendered!")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        if prompts_dir.exists():
            shutil.rmtree(prompts_dir)


if __name__ == "__main__":
    test_nested_prompts()
