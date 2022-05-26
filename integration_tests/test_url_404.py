import subprocess

from flask import Blueprint


def make_blueprint() -> Blueprint:
    return Blueprint("main", __name__)


def test(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        ["discolinks", "--json", "--url", "http://localhost:5000"],
        capture_output=True,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
