import subprocess

from flask import Blueprint, redirect

from . import util


def make_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return redirect("/foo")

    @blueprint.route("/foo")
    def foo():
        return redirect("/")

    return blueprint


def test_json(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(
            url="http://localhost:5000",
            json=True,
        ),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
