import json
import subprocess

import pytest
from flask import Blueprint

from . import util


def make_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return """
            <a href="/foo#bar">
            <a href="/foo#baz">
        """

    @blueprint.route("/foo")
    def foo():
        return """<h2 id="bar">"""

    return blueprint


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:5000",
        "http://localhost:5000#nx",
    ],
)
def test_json(http_server, url) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(
            url=url,
            json=True,
        ),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000": {
            "links": [
                {
                    "href": "/foo#bar",
                    "url": "http://localhost:5000/foo",
                    "results": [
                        {
                            "type": "response",
                            "status_code": 200,
                        }
                    ],
                },
                {
                    "href": "/foo#baz",
                    "url": "http://localhost:5000/foo",
                    "results": [
                        {
                            "type": "response",
                            "status_code": 200,
                        }
                    ],
                },
            ],
        },
        "http://localhost:5000/foo": {
            "links": [],
        },
    }
