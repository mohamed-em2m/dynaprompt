from dynaprompt import DynaPrompt


class TestInnerFolderAgents:
    def test_agents_folder_sub_agent_and_main_agent(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        sub_file = agents_dir / "sub_agent_instruction.md"
        sub_file.write_text("I am sub agent instruction.", encoding="utf-8")

        main_file = agents_dir / "main_agent_instruction.md"
        main_file.write_text(
            "Main Agent.\n"
            "Sub Instruction: {{ sub_agent_instruction }}\n"
            "With namespace: {{ agents.sub_agent_instruction }}",
            encoding="utf-8",
        )

        dp = DynaPrompt(settings_files=[str(tmp_path)])

        rendered = dp.agents.main_agent_instruction.render()
        assert "Main Agent." in rendered.text
        assert "Sub Instruction: I am sub agent instruction." in rendered.text
        assert "With namespace: I am sub agent instruction." in rendered.text


class TestUnusualVariableNames:
    def test_user_colon_main_with_variable(self, tmp_path):
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("User role: {{ user:main }}", encoding="utf-8")

        dp = DynaPrompt(
            settings_files=[str(prompt_file)], variables=[{"user:main": "admin_user"}]
        )
        rendered = dp.test_prompt.render()
        assert rendered.text == "User role: admin_user"

    def test_user_colon_main_unprovided_kept_as_is(self, tmp_path):
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("User role: {{ user:main }}", encoding="utf-8")

        dp = DynaPrompt(settings_files=[str(prompt_file)])
        rendered = dp.test_prompt.render()
        assert rendered.text == "User role: {{ user:main }}"

    def test_double_curly_hello_world_kept_as_is(self, tmp_path):
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text('Literal: {{"hello world"}}', encoding="utf-8")

        dp = DynaPrompt(settings_files=[str(prompt_file)])
        rendered = dp.test_prompt.render()
        assert "hello world" in rendered.text
        # Should not raise syntax error

    def test_spaces_in_var_tag_kept_as_is(self, tmp_path):
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("Tag: {{ hello world }}", encoding="utf-8")

        dp = DynaPrompt(settings_files=[str(prompt_file)])
        rendered = dp.test_prompt.render()
        assert rendered.text == "Tag: {{ hello world }}"
