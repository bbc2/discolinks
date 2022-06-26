import json
import subprocess

from flask import Blueprint, redirect

from . import util


def make_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return """
            <a href="/foo">
            <a href="/bar">
        """

    @blueprint.route("/foo")
    def foo():
        return redirect("/baz")

    @blueprint.route("/bar")
    def bar():
        return redirect("/nx")

    @blueprint.route("/baz")
    def baz():
        return """<a href="/">\n"""

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
        📂 Results: 5 links (3 ok, 2 failed)
        ├── 📄 http://localhost:5000
        │   └── 🔗 /bar: 302 → 404
        └── 📄 http://localhost:5000/
            └── 🔗 /bar: 302 → 404
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
                            "type": "redirect",
                            "status_code": 302,
                            "value": "/baz",
                            "url": "http://localhost:5000/baz",
                        },
                        {
                            "type": "response",
                            "status_code": 200,
                        },
                    ],
                },
                {
                    "href": "/bar",
                    "url": "http://localhost:5000/bar",
                    "results": [
                        {
                            "type": "redirect",
                            "status_code": 302,
                            "value": "/nx",
                            "url": "http://localhost:5000/nx",
                        },
                        {
                            "type": "response",
                            "status_code": 404,
                        },
                    ],
                },
            ],
        },
        "http://localhost:5000/": {
            "links": [
                {
                    "href": "/foo",
                    "url": "http://localhost:5000/foo",
                    "results": [
                        {
                            "type": "redirect",
                            "status_code": 302,
                            "value": "/baz",
                            "url": "http://localhost:5000/baz",
                        },
                        {
                            "type": "response",
                            "status_code": 200,
                        },
                    ],
                },
                {
                    "href": "/bar",
                    "url": "http://localhost:5000/bar",
                    "results": [
                        {
                            "type": "redirect",
                            "status_code": 302,
                            "value": "/nx",
                            "url": "http://localhost:5000/nx",
                        },
                        {
                            "type": "response",
                            "status_code": 404,
                        },
                    ],
                },
            ],
        },
        "http://localhost:5000/baz": {
            "links": [
                {
                    "href": "/",
                    "url": "http://localhost:5000/",
                    "results": [
                        {
                            "type": "response",
                            "status_code": 200,
                        },
                    ],
                },
            ],
        },
    }
