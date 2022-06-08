import subprocess

from . import util


def test_json() -> None:
    result = subprocess.run(
        util.command(url="http://localhost:1", json=True),
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
