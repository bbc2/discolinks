import json
import subprocess

from flask import Blueprint, abort, redirect

from . import util


def make_blueprint(last_redirect_ok: bool) -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.route("/")
    def root():
        return redirect("/foo")

    @blueprint.route("/foo")
    def foo():
        return redirect("/bar")

    @blueprint.route("/bar")
    def bar():
        if last_redirect_ok:
            return """<a href="/">\n"""
        else:
            abort(404)

    return blueprint


def test_json_ok(http_server) -> None:
    http_server(blueprint=make_blueprint(last_redirect_ok=True), port=5000)

    result = subprocess.run(
        util.command(
            url="http://localhost:5000",
            json=True,
        ),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout.decode()) == {
        "http://localhost:5000/bar": {
            "links": [
                {
                    "href": "/",
                    "url": "http://localhost:5000/",
                    "results": [
                        {
                            "type": "redirect",
                            "status_code": 302,
                            "value": "/foo",
                            "url": "http://localhost:5000/foo",
                        },
                        {
                            "type": "redirect",
                            "status_code": 302,
                            "value": "/bar",
                            "url": "http://localhost:5000/bar",
                        },
                        {
                            "type": "response",
                            "status_code": 200,
                        },
                    ],
                },
            ],
        },
    }


def test_json_not_found(http_server) -> None:
    http_server(blueprint=make_blueprint(last_redirect_ok=False), port=5000)

    result = subprocess.run(
        util.command(
            url="http://localhost:5000",
            json=True,
        ),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
