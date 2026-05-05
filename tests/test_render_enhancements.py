from pydantic import BaseModel

from dynaprompt.nodes import PromptNode


class UserProfile(BaseModel):
    name: str
    age: int


def test_render_with_positional_dict():
    # Setup a dummy prompt
    # Manually register a prompt for testing

    node = PromptNode(name="test", text="Hello {{ name }}! You are {{ age }}.")

    # Test rendering with a positional dict
    data = {"name": "Emam", "age": 30}
    rendered = node.render(data)
    assert rendered.text == "Hello Emam! You are 30."


def test_render_with_pydantic_model_in_dict():
    from dynaprompt.nodes import PromptNode

    node = PromptNode(name="test", text="User: {{ user.name }}, Age: {{ user.age }}")

    user = UserProfile(name="Emam", age=30)
    # Pass user in a dict
    rendered = node.render(user=user)

    # The user object should have been converted to a dict, so {{ user.name }} works
    assert rendered.text == "User: Emam, Age: 30"


def test_render_with_pydantic_model_deep_flatten():
    from dynaprompt.nodes import PromptNode

    node = PromptNode(name="test", text="Deep: {{ data.users[0].name }}")

    user = UserProfile(name="Emam", age=30)
    rendered = node.render(data={"users": [user]})

    assert rendered.text == "Deep: Emam"


def test_render_with_pydantic_model_json_serialization():
    from dynaprompt.nodes import PromptNode

    # When key contains 'json', it should be a string
    node = PromptNode(name="test", text="JSON: {{ user_json }}")

    user = UserProfile(name="Emam", age=30)
    rendered = node.render(user_json=user)

    # Should be a JSON string
    assert '"name": "Emam"' in rendered.text
    assert '"age": 30' in rendered.text
