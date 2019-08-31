import ujson
import subprocess
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--remote", action="store_true")
    parser.addoption("--stage", action="store")


@pytest.fixture
def make_sls_cmd(pytestconfig):
    def _make(function_name, event_path):
        cmd = ["pipenv", "run", "serverless", "invoke"]
        if not pytestconfig.getoption("remote"):
            cmd.append("local")
        if pytestconfig.getoption("stage"):
            if pytestconfig.getoption("stage") == "prod":
                raise SystemExit("Do not run tests against production")
            cmd.append("--stage")
            cmd.append(pytestconfig.getoption("stage"))
        cmd.append("-f")
        cmd.append(function_name)
        cmd.append("-p")
        cmd.append(event_path)

        return cmd

    return _make


@pytest.fixture
def run_sls_cmd(make_sls_cmd):
    def _run(function_name, event_path):
        cmd = make_sls_cmd(function_name, event_path)
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        return ujson.loads(result.stdout)

    return _run


@pytest.fixture
def generate_event(tmp_path):
    def _generate(body: dict = None, name="event", path_parameters=None):
        event_path: Path = tmp_path / f"{name}.json"
        event_data = {
            "body": ujson.dumps(body),
            "requestContext": {"identity": {"cognitoIdentityId": "USER-SUB-1234"}},
            "pathParameters": path_parameters,
        }
        with event_path.open("w") as event_file:
            ujson.dump(event_data, event_file)
        return str(event_path.absolute())

    return _generate
