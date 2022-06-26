import json
import subprocess

from flask import Blueprint, abort

from . import util


def make_blueprint_with_link(link: str) -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return f"""<a href="{link}">\n"""

    return blueprint


def make_blueprint_no_head() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/", methods=["HEAD"])
    def root_head():
        abort(405)

    @blueprint.route("/", methods=["GET"])
    def root_get():
        return ""

    return blueprint


def test_json(http_server) -> None:
    http_server(
        blueprint=make_blueprint_with_link(link="http://localhost:5001"),
        port=5000,
    )
    http_server(blueprint=make_blueprint_no_head(), port=5001)

    result = subprocess.run(
        util.command(url="http://localhost:5000", json=True),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000": {
            "links": [
                {
                    "href": "http://localhost:5001",
                    "url": "http://localhost:5001",
                    "results": [
                        {
                            "type": "response",
                            "status_code": 200,
                        }
                    ],
                },
            ],
        },
    }
