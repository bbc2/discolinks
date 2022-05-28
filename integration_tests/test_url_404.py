import subprocess

from flask import Blueprint

from . import util


def make_blueprint() -> Blueprint:
    return Blueprint("main", __name__)


def test(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(url="http://localhost:5000", json=True),
        capture_output=True,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
