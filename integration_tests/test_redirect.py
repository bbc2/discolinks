import json
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
        return """<a href="/">\n"""

    return blueprint


def test_json(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(
            url="http://localhost:5000",
            json=True,
        ),
        capture_output=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000/": {
            "status_code": 200,
            "origins": [
                {
                    "href": "/",
                    "page": "http://localhost:5000",
                },
                {
                    "href": "/",
                    "page": "http://localhost:5000/",
                },
            ],
        },
    }