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
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == util.output_str(
        """
        📂 Results: 1 links (0 ok, 1 failed)
        └── 📄 http://localhost:5000
            └── 🔗 /foo: 404
        """
    )


def test_json(http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(url="http://localhost:5000", json=True),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000": {
            "links": [
                {
                    "href": "/foo",
                    "url": "http://localhost:5000/foo",
                    "results": [
                        {
                            "type": "response",
                            "status_code": 404,
                        }
                    ],
                },
            ],
        },
    }
