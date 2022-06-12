import json
import subprocess

import pytest
from flask import Blueprint

from . import util


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
        util.command(url="http://localhost:5000"),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert result.stdout.decode() == ""


@pytest.mark.parametrize(
    "max_parallel_requests",
    [
        None,
        1,
        4,
    ],
)
def test_json(max_parallel_requests: int, http_server) -> None:
    http_server(blueprint=make_blueprint(), port=5000)

    result = subprocess.run(
        util.command(
            url="http://localhost:5000",
            json=True,
            max_parallel_requests=max_parallel_requests,
        ),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000": {
            "links": [
                {
                    "href": "/foo",
                    "destination": {
                        "url": "http://localhost:5000/foo",
                        "status_code": 200,
                    },
                },
            ],
        },
        "http://localhost:5000/": {
            "links": [
                {
                    "href": "/foo",
                    "destination": {
                        "url": "http://localhost:5000/foo",
                        "status_code": 200,
                    },
                },
            ],
        },
        "http://localhost:5000/foo": {
            "links": [
                {
                    "href": "/",
                    "destination": {
                        "url": "http://localhost:5000/",
                        "status_code": 200,
                    },
                },
            ],
        },
    }
