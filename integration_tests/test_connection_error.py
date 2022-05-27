import subprocess


def test_json() -> None:
    result = subprocess.run(
        ["discolinks", "--json", "--url", "http://localhost:1"],
        capture_output=True,
    )

    assert result.returncode == 1
    assert result.stdout.decode() == ""
