import json
import subprocess

from flask import Blueprint


def make_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return """<a href="/foo">\n"""

    @blueprint.route("/foo")
    def foo():
        return """<a href="/">\n"""

    return blueprint


def test_text(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        ["discolinks", "--url", "http://localhost:5000"],
        capture_output=True,
    )

    assert result.returncode == 0
    assert result.stdout.decode() == ""


def test_json(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        ["discolinks", "--json", "--url", "http://localhost:5000"],
        capture_output=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000/": {
            "status_code": 200,
            "origins": [
                {
                    "href": "/",
                    "page": "http://localhost:5000/foo",
                },
            ],
        },
        "http://localhost:5000/foo": {
            "status_code": 200,
            "origins": [
                {
                    "page": "http://localhost:5000",
                    "href": "/foo",
                },
                {
                    "page": "http://localhost:5000/",
                    "href": "/foo",
                },
            ],
        },
    }
