import subprocess

import pytest


@pytest.mark.parametrize(
    "invocation",
    [
        ["discolinks"],
        ["python", "-m", "discolinks"],
    ],
)
def test_version_module(invocation):
    result = subprocess.run(
        [*invocation, "--version"],
        stdout=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert result.stdout.decode().startswith("discolinks version ")
