import inspect
from typing import Optional, Sequence


def output_str(s: str) -> str:
    clean_str = inspect.cleandoc(s)
    return f"{clean_str}\n"


def command(
    url: str,
    verbose: Optional[bool] = None,
    json: Optional[bool] = None,
    max_parallel_requests: Optional[int] = None,
) -> Sequence[str]:
    """
    Generate command-line strings based on function parameters.

    The parameters and their default values are as close to the real CLI as possible, so
    that the function call looks pretty much the same as a CLI invocation.
    """

    cli = ["discolinks"]

    if verbose:
        cli += ["--verbose"]

    if json:
        cli += ["--json"]

    if max_parallel_requests is not None:
        cli += ["--max-parallel-requests", str(max_parallel_requests)]

    cli += ["--url", url]

    return cli
