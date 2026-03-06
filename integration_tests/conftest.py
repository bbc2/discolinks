from threading import Thread

import pytest
from flask import Blueprint
from werkzeug.serving import make_server

from . import server


@pytest.fixture
def http_server():
    created_servers = {}

    def _make_server(blueprint: Blueprint, port: int) -> None:
        app = server.create_app(blueprint=blueprint)
        srv = make_server("127.0.0.1", port, app)
        thread = Thread(target=srv.serve_forever)
        thread.daemon = True
        thread.start()
        created_servers[port] = (thread, srv)

    yield _make_server

    for thread, srv in created_servers.values():
        srv.shutdown()
        thread.join()
