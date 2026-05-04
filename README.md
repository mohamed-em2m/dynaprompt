
<p align="center"><img src="/art/dyna-prompt.png" alt="dyna-prompt. new logo"></p>

> **dyna-prompt** - Configuration Management for Python.

[![MIT License](https://img.shields.io/badge/license-MIT-007EC7.svg?style=flat-square)](/LICENSE) [![PyPI](https://img.shields.io/pypi/v/dynaconf.svg)](https://pypi.python.org/pypi/dynaconf) [![PyPI](https://img.shields.io/pypi/pyversions/dynaconf.svg)]() ![PyPI - Downloads](https://img.shields.io/pypi/dm/dynaconf.svg?label=pip%20installs&logo=python) [![CI](https://github.com/dynaconf/dynaconf/actions/workflows/main.yml/badge.svg)](https://github.com/dynaconf/dynaconf/actions/workflows/main.yml) [![codecov](https://codecov.io/gh/dynaconf/dynaconf/branch/master/graph/badge.svg)](https://codecov.io/gh/dynaconf/dynaconf) [![Codacy Badge](https://app.codacy.com/project/badge/Grade/3fb2de98464442f99a7663181803b400)](https://www.codacy.com/gh/dynaconf/dynaconf/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dynaconf/dynaconf&amp;utm_campaign=Badge_Grade)  ![GitHub stars](https://img.shields.io/github/stars/dynaconf/dynaconf.svg) ![GitHub Release Date](https://img.shields.io/github/release-date/dynaconf/dynaconf.svg) ![GitHub commits since latest release](https://img.shields.io/github/commits-since/dynaconf/dynaconf/latest.svg) ![GitHub last commit](https://img.shields.io/github/last-commit/dynaconf/dynaconf.svg) [![Code Style Black](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

![GitHub issues](https://img.shields.io/github/issues/dynaconf/dynaconf.svg) [![User Forum](https://img.shields.io/badge/users-forum-blue.svg?logo=googlechat)](https://github.com/dynaconf/dynaconf/discussions) [![Join the chat at https://gitter.im/dynaconf/dev](https://badges.gitter.im/dynaconf/dev.svg)](https://gitter.im/dynaconf/dev?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![ Matrix](https://img.shields.io/badge/dev-room-blue.svg?logo=matrix)](https://matrix.to/#/#dynaconf:matrix.org)

## Features

- Inspired by the [12-factor application guide](https://12factor.net/config)
- Settings management (default values, validation, parsing, templating)
- Protection of sensitive information (passwords/tokens)
- Multiple file formats `toml|yaml|json|ini|py` and also customizable loaders.
- Full support for environment variables to override existing settings (dotenv support included).
- Optional layered system for multi environments `[default, development, testing, production]`
- Built-in support for Hashicorp Vault and Redis as settings and secrets storage.
- Built-in extensions for **Django** and **Flask** web frameworks.
- CLI for common operations such as `init, list, write, validate, export`.
- full docs on https://dynaconf.com

### Install

```bash
$ pip install dynaconf
```

#### Initialize Dynaconf on project root directory

```plain
$ cd path/to/your/project/

$ dynaconf init -f toml

⚙️  Configuring your Dynaconf environment
------------------------------------------
🐍 The file `config.py` was generated.

🎛️  settings.toml created to hold your settings.

🔑 .secrets.toml created to hold your secrets.

🙈 the .secrets.* is also included in `.gitignore`
  beware to not push your secrets to a public repo.

🎉 Dynaconf is configured! read more on https://dynaconf.com
```

> **TIP:** You can select `toml|yaml|json|ini|py` on `dynaconf init -f <fileformat>`  **toml** is the default and also the most recommended format for configuration.

#### Dynaconf init creates the following files

```plain
.
├── config.py       # This is from where you import your settings object (required)
├── .secrets.toml   # This is to hold sensitive data like passwords and tokens (optional)
└── settings.toml   # This is to hold your application settings (optional)
```

On the file `config.py` Dynaconf init generates the following boilerplate

```py
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",  # export envvars with `export DYNACONF_FOO=bar`.
    settings_files=['settings.yaml', '.secrets.yaml'],  # Load files in the given order.
)
```

> **TIP:** You can create the files yourself instead of using the `init` command as shown above and you can give any name you want instead of the default `config.py` (the file must be in your importable python path) - See more options that you can pass to `Dynaconf` class initializer on https://dynaconf.com


#### Using Dynaconf

Put your settings on `settings.{toml|yaml|ini|json|py}`

```toml
username = "admin"
port = 5555
database = {name='mydb', schema='main'}
```

Put sensitive information on `.secrets.{toml|yaml|ini|json|py}`

```toml
password = "secret123"
```

> **IMPORTANT:** `dynaconf init` command puts the `.secrets.*` in your `.gitignore` to avoid it to be exposed on public repos but it is your responsibility to keep it safe in your local environment, also the recommendation for production environments is to use the built-in support for Hashicorp Vault service for password and tokens.


Optionally you can now use environment variables to override values per execution or per environment.

```bash
# override `port` from settings.toml file and automatically casts as `int` value.
export DYNACONF_PORT=9900
```


On your code import the `settings` object

```py
from path.to.project.config import settings

# Reading the settings

settings.username == "admin"  # dot notation with multi nesting support
settings.PORT == 9900  # case insensitive
settings['password'] == "secret123"  # dict like access
settings.get("nonexisting", "default value")  # Default values just like a dict
settings.databases.name == "mydb"  # Nested key traversing
settings['databases.schema'] == "main"  # Nested key traversing
```

## DynaPrompt

DynaPrompt is a powerful, lazy-loading prompt configuration manager built directly on Dynaconf's principles. It offers a structured way to manage, version, and render LLM prompts while separating prompt text from configuration metadata.

### Features
- **File-based Prompt Management**: Write prompt templates in clean Markdown (`.md` or `.txt`) with YAML frontmatter, or group multiple prompts in a `prompts.toml` file.
- **Auto-Discovery & Companion Files**: Pass a directory like `settings_files=["prompts/"]` and DynaPrompt automatically loads all `.md` files in it. It will also auto-discover a sibling `prompts.toml` companion file allowing you to manage metadata (like `model`, `temperature`, `max_tokens`) separately from your templates.
- **Automatic Name Sanitization**: Filenames like `Call Analysis.md` are automatically normalized into clean, snake-case identifiers (e.g. `prompts.call_analysis`).
- **Prefix Filtering**: Use `file_prefix="gpt_"` to only load files starting with a prefix, stripping it for a clean API (e.g., `prompts.support` instead of `gpt_support`).
- **Lazy Loading**: Zero I/O at instantiation. Files are only loaded when you access a prompt for the first time.
- **Environment Layering**: Render prompts differently per environment (`development`, `production`, etc.) without duplicating templates.
- **Validation & Hooks**: Enforce constraints on rendered prompts and intercept rendering using powerful hook systems.

### Usage
```python
from dynaprompt import DynaPrompt

prompts = DynaPrompt(
    settings_files=["prompts/"], # Can be a directory of .md files or .toml files
    environments=True
)

# Rendering a template (e.g., loaded from prompts/customer_support.md)
rendered = prompts.customer_support.render(user_name="Ahmed", issue="Payment failed")

print(rendered.text)
print(rendered.config["model"])
```

### Schema Auto-loading
DynaPrompt can automatically detect and register schemas from Python files or JSON files included in your `settings_files`.

- **Python Files**: All classes defined in `.py` files are registered. This is perfect for **Pydantic** models.
- **JSON Files**: Entire JSON objects are registered under their filename stem.

```python
# Pass a directory containing prompts.toml and schemas.py
prompts = DynaPrompt(settings_files=["prompts/"])

# Access auto-loaded Pydantic models directly as attributes
schema = prompts.AnalysisSchema
```

### Attribute Access & Tab-Completion
All loaded **prompts** and **schemas** are available as direct attributes of the `DynaPrompt` instance. 

- **Tab-Completion**: Use `dir(prompts)` or hit `Tab` in your IDE/IPython to see all available prompts and schemas.
- **Unified API**: No need to distinguish between where a schema or prompt came from—if it's in your settings folder, it's an attribute.

```python
# Access a prompt
rendered = prompts.customer_support.render(...)

# Access a schema (loaded from schemas.py or schema.json)
schema = prompts.UserProfile
```

## More

- Settings Schema Validation
- Custom Settings Loaders
- Vault Services
- Template substitutions
- etc...

There is a lot more you can do, **read the docs:** http://dynaconf.com

## Contribute

Main discussions happens on [Discussions Tab](https://github.com/dynaconf/dynaconf/discussions) learn more about how to get involved on [CONTRIBUTING.md guide](CONTRIBUTING.md)

## More

If you are looking for something similar to Dynaconf to use in your Rust projects: https://github.com/rubik/hydroconf

And a special thanks to [Caneco](https://twitter.com/caneco) for the logo.
