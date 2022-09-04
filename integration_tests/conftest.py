from multiprocessing import Process

import pytest
from flask import Blueprint

from . import server


def launch_process(target, kwargs) -> Process:
    process = Process(target=target, kwargs=kwargs)
    process.start()
    return process


@pytest.fixture
def http_server():
    created_servers = {}

    def _make_server(blueprint: Blueprint, port: int) -> Process:
        app = server.create_app(blueprint=blueprint)
        process = launch_process(target=app.run, kwargs={"port": port})
        created_servers[port] = process
        return process

    yield _make_server

    errors = []
    for (port, process) in created_servers.items():
        if process.exitcode is not None:
            errors.append(f"Server failure for port {port}")
        process.terminate()
    assert not errors
