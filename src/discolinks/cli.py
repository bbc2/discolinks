import asyncio
import logging
from typing import AbstractSet, Optional
from urllib.parse import urldefrag, urlparse

import attrs
import click
import rich.console
from rich.logging import RichHandler

from . import analyzer, export, html, outcome, text
from .core import Url
from .link_store import LinkStore, UrlInfo
from .monitor import Monitor, new_monitor
from .requester import Requester

logger = logging.getLogger(__name__)


def parse_url_arg(url: str) -> Optional[Url]:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    parsed = urlparse(url)

    if not parsed.netloc:
        return None

    (url, _) = urldefrag(url)
    return Url.from_str(url)


@attrs.frozen
class InfoConverter(outcome.Converter[UrlInfo]):
    url: Url
    with_links: bool

    def convert_redirect(self, redirect: outcome.Redirect) -> UrlInfo:
        return UrlInfo(result=redirect, links=None)

    def convert_page(self, page: outcome.Page) -> UrlInfo:
        if self.with_links:
            links = html.get_links(body=page.body, url=self.url)
            return UrlInfo(result=page, links=links)
        else:
            return UrlInfo(result=page, links=None)

    def convert_request_error(self, error: outcome.RequestError) -> UrlInfo:
        return UrlInfo(result=error, links=None)


def get_url_info(url: Url, result: outcome.Result, with_links: bool) -> UrlInfo:
    converter = InfoConverter(url=url, with_links=with_links)
    return result.convert_with(converter)


async def investigate_url(
    requester: Requester,
    link_store: LinkStore,
    start_url: Url,
    url: Url,
) -> AbstractSet[Url]:
    """
    Follow HTTP link and return new links if any are found.

    For external websites this only does a `HEAD` to know if the link is broken or not, so
    no new links are returned.
    """

    if url.netloc != start_url.netloc:
        result = await requester.get(url=url, use_head=True)

        if result.status_code() == 405:  # method not allowed
            result = await requester.get(url=url)

        return link_store.add_page(
            url=url,
            info=get_url_info(result=result, url=url, with_links=False),
        )

    result = await requester.get(url=url)

    return link_store.add_page(
        url=url,
        info=get_url_info(result=result, url=url, with_links=result.ok()),
    )


async def work(
    queue: asyncio.Queue[Url],
    requester: Requester,
    link_store: LinkStore,
    monitor: Monitor,
    start_url: Url,
):
    while True:
        task_url = await queue.get()
        monitor.on_task_start(queued=queue.qsize())
        try:
            new_urls = await investigate_url(
                requester=requester,
                link_store=link_store,
                start_url=start_url,
                url=task_url,
            )
            for url in new_urls:
                queue.put_nowait(url)
        finally:
            queue.task_done()

        monitor.on_task_done(
            queued=queue.qsize(),
            result=link_store.get_url_infos()[task_url].result,
        )


async def find_links(
    max_parallel_requests: int,
    requester: Requester,
    link_store: LinkStore,
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
                link_store=link_store,
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
    link_store: LinkStore,
    monitor: Monitor,
    start_url: Url,
):
    requester = Requester()
    next_url: Optional[Url] = start_url

    while next_url is not None:
        url = next_url
        result = await requester.get(url)
        next_url = result.redirect_url()
        new_urls = link_store.add_page(
            url=url,
            info=get_url_info(result=result, url=url, with_links=True),
        )
        if next_url is not None:
            monitor.print(f"redirected to {next_url}")

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
        link_store=link_store,
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
def main(verbose: bool, max_parallel_requests: int, to_json: bool, url: str) -> None:
    console = rich.console.Console(stderr=True)
    main_logger = logging.getLogger("discolinks")
    level = logging.DEBUG if verbose else logging.WARNING
    main_logger.setLevel(level)
    main_logger.addHandler(RichHandler(console=console, show_time=False))

    start_url = parse_url_arg(url)

    if start_url is None:
        logger.error("Invalid URL: %s", url)
        exit(1)

    link_store = LinkStore()
    with new_monitor(console=console) as monitor:
        asyncio.run(
            main_async(
                max_parallel_requests=max_parallel_requests,
                link_store=link_store,
                monitor=monitor,
                start_url=start_url,
            )
        )

    url_infos = link_store.get_url_infos()
    pages = analyzer.analyze(url_infos)
    ok = all(link.ok() for (_, page) in pages.items() for link in page.links)

    if to_json:
        print(export.dump_json(pages=pages))
        exit(0 if ok else 1)

    text.print_results(pages=pages)
    exit(0 if ok else 1)
