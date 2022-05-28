import inspect
from typing import Sequence


def output_str(s: str) -> str:
    clean_str = inspect.cleandoc(s)
    return f"{clean_str}\n"


def command(
    url: str,
    verbose: bool = None,
    json: bool = None,
    max_parallel_requests: int = None,
) -> Sequence[str]:
    cli = ["discolinks"]

    if verbose:
        cli += ["--verbose"]

    if json:
        cli += ["--json"]

    if max_parallel_requests is not None:
        cli += ["--max-parallel-requests", str(max_parallel_requests)]

    cli += ["--url", url]

    return cli
