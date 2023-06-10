import json
import subprocess

from flask import Blueprint

from . import util


def make_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return """
            <a href="/foo"></a>
        """

    @blueprint.route("/foo")
    def foo():
        return """
            <a href="/nonexistent"></a>
        """

    return blueprint


def test_ok(http_server) -> None:
    http_server(make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(url="http://localhost:5000", exclude=["foo"], json=True),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000": {
            "links": [
                {
                    "href": "/foo",
                    "url": "http://localhost:5000/foo",
                    "results": [
                        {
                            "type": "excluded",
                        },
                    ],
                },
            ],
        },
    }


def test_bad_regex(http_server) -> None:
    http_server(make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(url="http://localhost:5000", exclude=["("], json=True),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
