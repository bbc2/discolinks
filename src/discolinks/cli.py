import asyncio
import logging
from typing import Optional
from urllib.parse import urldefrag, urlparse

import click
import rich.console
from rich.logging import RichHandler

from . import analyzer, export, text
from .core import Url
from .link_extractor import get_links
from .monitor import Monitor, new_monitor
from .requester import Requester
from .url_store import UrlInfo, UrlStore
from .worker import work

logger = logging.getLogger(__name__)


def parse_url_arg(url: str) -> Optional[Url]:
    """
    Parse a string representing a URL.

    This is intended for the URL provided as argument to the program. For example, if the
    scheme is missing, it assumes the user meant to use the `http` scheme, like many other
    programs using web URLs.
    """

    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    parsed = urlparse(url)

    if not parsed.netloc:
        return None

    (url, _) = urldefrag(url)
    return Url.from_str(url)


async def find_links(
    max_parallel_requests: int,
    requester: Requester,
    url_store: UrlStore,
    monitor: Monitor,
    start_url: Url,
    first_urls: frozenset[Url],
) -> None:
    queue: asyncio.Queue[Url] = asyncio.Queue()

    for url in first_urls:
        queue.put_nowait(url)

    workers: list[asyncio.Task] = []

    for _ in range(max_parallel_requests):
        worker = asyncio.create_task(
            work(
                queue=queue,
                requester=requester,
                url_store=url_store,
                monitor=monitor,
                start_url=start_url,
            ),
        )
        workers.append(worker)

    # Wait for queue processing to finish, or for any worker to finish (which only happens
    # if that worker raised an exception).
    await asyncio.wait(
        [queue.join(), *workers],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for worker in workers:
        worker.cancel()

    try:
        await asyncio.gather(*workers)  # ← worker exceptions raised here
    except asyncio.CancelledError:
        pass


async def main_async(
    max_parallel_requests: int,
    url_store: UrlStore,
    monitor: Monitor,
    start_url: Url,
):
    requester = Requester()
    next_url: Optional[Url] = start_url

    while next_url is not None:
        url = next_url
        result = await requester.get(url)
        next_url = result.redirect_url()
        new_urls = url_store.add_page(
            url=url,
            info=UrlInfo(result=result, links=get_links(url=url, result=result)),
        )
        if next_url is not None:
            logger.info(f"Redirected to {next_url}")

            if next_url not in new_urls:
                logger.error("Detected circular redirects. Aborting.")
                exit(1)

    error_msg = result.error_msg()
    if error_msg is not None:
        logger.error("%s", error_msg)
        exit(1)

    if not result.ok():
        logger.error("Bad response status code: %d", result.status_code())
        exit(1)

    await find_links(
        max_parallel_requests=max_parallel_requests,
        requester=requester,
        url_store=url_store,
        monitor=monitor,
        start_url=url,
        first_urls=new_urls,
    )


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    help="Increase verbosity to show debug messages.",
)
@click.option(
    "--max-parallel-requests",
    default=4,
    type=click.IntRange(min=1),
    help="Maximum of requests which can be in-flight at any given time.",
)
@click.option(
    "--json",
    "to_json",
    is_flag=True,
    help="Export results as JSON to the standard output.",
)
@click.option("--url", required=True, help="URL where crawling will start.")
@click.version_option(
    prog_name="discolinks",
    message="%(prog)s version %(version)s",
)
def main(verbose: bool, max_parallel_requests: int, to_json: bool, url: str) -> None:
    console = rich.console.Console(stderr=True)
    main_logger = logging.getLogger("discolinks")
    level = logging.DEBUG if verbose else logging.INFO
    main_logger.setLevel(level)
    main_logger.addHandler(RichHandler(console=console, show_time=False))

    start_url = parse_url_arg(url)

    if start_url is None:
        logger.error("Invalid URL: %s", url)
        exit(1)

    url_store = UrlStore()

    try:
        with new_monitor(console=console) as monitor:
            asyncio.run(
                main_async(
                    max_parallel_requests=max_parallel_requests,
                    url_store=url_store,
                    monitor=monitor,
                    start_url=start_url,
                )
            )
    except KeyboardInterrupt:
        logger.warning("Interrupted.")
        interrupted = True
    except Exception as exc:
        logger.exception(exc)
        interrupted = True
    else:
        interrupted = False

    url_infos = url_store.get_url_infos()
    analysis = analyzer.analyze(url_infos)
    ok = not interrupted and analysis.ok()

    if to_json:
        print(export.dump_json(analysis=analysis))
    else:
        text.print_results(analysis=analysis)

    exit(0 if ok else 1)
