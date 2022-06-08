import json
import subprocess

from flask import Blueprint

from . import util


def make_blueprint(link: str) -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return f"""<a href="{link}">\n"""

    return blueprint


def test_json(http_server) -> None:
    http_server(blueprint=make_blueprint(link="http://localhost:5001"), port=5000)
    http_server(blueprint=make_blueprint(link="http://localhost:5002"), port=5001)

    result = subprocess.run(
        util.command(url="http://localhost:5000", json=True),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5001": {
            "status_code": 200,
            "origins": [
                {
                    "page": "http://localhost:5000",
                    "href": "http://localhost:5001",
                },
            ],
        },
    }
