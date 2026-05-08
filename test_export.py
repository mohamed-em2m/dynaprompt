import pathlib

from dynaprompt import DynaPrompt

p = pathlib.Path("test_prompts/google")
p.mkdir(parents=True, exist_ok=True)
(p / "gemini.md").write_text("---\nmodel: test\n---\nHello {{ name }}!")

dp = DynaPrompt(settings_files=["test_prompts"], auto_export=True)
# trigger setup
dp.google.gemini

print("Export created:", pathlib.Path("pyprompts.toml").exists())
print(pathlib.Path("pyprompts.toml").read_text())
