import os
import tempfile
from pathlib import Path

import pytest

from vcti.util.app_environment import AppEnvironment  # Adjust if needed
from vcti.util.app_environment import Variable, VariableType


@pytest.fixture
def env_vars():
    os.environ["TESTAPP_FLAG_VAR"] = "true"
    os.environ["TESTAPP_STRING_VAR"] = "hello"
    os.environ["TESTAPP_INT_VAR"] = "42"
    os.environ["TESTAPP_FLOAT_VAR"] = "3.14"
    os.environ["TESTAPP_PATH_VAR"] = tempfile.gettempdir()
    yield
    for key in list(os.environ):
        if key.startswith("TESTAPP_"):
            del os.environ[key]


def test_app_environment_with_env_vars(env_vars):
    variables = [
        Variable(id="flag_var", type=VariableType.FLAG, default=False),
        Variable(id="string_var", type=VariableType.STRING, default="default"),
        Variable(id="int_var", type=VariableType.INT, default=0),
        Variable(id="float_var", type=VariableType.FLOAT, default=0.0),
        Variable(id="path_var", type=VariableType.PATH, default=Path(".")),
    ]

    env = AppEnvironment(variables, prefix="TESTAPP_")

    assert env.get("flag_var") is True
    assert env.get("string_var") == "hello"
    assert env.get("int_var") == 42
    assert env.get("float_var") == 3.14
    assert env.get("path_var") == Path(tempfile.gettempdir())


def test_app_environment_with_defaults():
    temp_path = Path(tempfile.gettempdir())
    variables = [
        Variable(id="missing_flag", type=VariableType.FLAG, default=False),
        Variable(id="missing_string", type=VariableType.STRING, default="abc"),
        Variable(id="missing_int", type=VariableType.INT, default=123),
        Variable(id="missing_float", type=VariableType.FLOAT, default=1.23),
        Variable(id="missing_path", type=VariableType.PATH, default=temp_path),
    ]

    env = AppEnvironment(variables, prefix="UNUSED_PREFIX_")

    assert env.get("missing_flag") is False
    assert env.get("missing_string") == "abc"
    assert env.get("missing_int") == 123
    assert env.get("missing_float") == 1.23
    assert env.get("missing_path") == temp_path


def test_metadata_and_exports():
    variables = [
        Variable(id="demo_var", type=VariableType.STRING, default="abc"),
    ]
    env = AppEnvironment(variables, prefix="APP_")

    var_info = env.variable_info("demo_var")
    assert isinstance(var_info, dict)
    assert var_info["id"] == "demo_var"
    assert var_info["value"] == "abc"
    assert var_info["payload"] is None
    assert var_info["name"] == "APP_DEMO_VAR"

    # Ensure export methods work without exception
    json_str = env.as_json()
    csv_str = env.as_csv()
    md_str = env.as_markdown()

    assert "demo_var" in json_str
    assert "demo_var" in csv_str
    assert "| id" in md_str
