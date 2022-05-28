import json
import subprocess

from flask import Blueprint

from . import util


def make_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return """<a href="/foo">\n"""

    return blueprint


def test_text(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(url="http://localhost:5000"),
        capture_output=True,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == util.output_str(
        """
        http://localhost:5000/foo
          status code: 404
          origins:
            http://localhost:5000: /foo
        """
    )


def test_json(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(url="http://localhost:5000", json=True),
        capture_output=True,
    )

    assert result.returncode == 1
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000/foo": {
            "status_code": 404,
            "origins": [
                {
                    "page": "http://localhost:5000",
                    "href": "/foo",
                },
            ],
        },
    }
