import asyncio
import logging
from typing import AbstractSet, Optional
from urllib.parse import urldefrag, urlparse

import attrs
import click

from . import export, html
from .core import Url
from .link_store import LinkStore, PageLink, UrlInfo
from .requester import GetResponse, Requester, RequestError

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
class LinkResult:
    status_code: Optional[int]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)


@attrs.frozen
class LinkResponse:
    result: LinkResult
    response: Optional[GetResponse]


async def request_link_head(requester: Requester, url: Url) -> LinkResult:
    try:
        response = await requester.head(url)
    except RequestError:
        return LinkResult(status_code=None)

    return LinkResult(status_code=response.status_code)


async def request_link_get(requester: Requester, url: Url) -> LinkResponse:
    try:
        response = await requester.get(url)
    except RequestError:
        return LinkResponse(
            result=LinkResult(status_code=None),
            response=None,
        )

    return LinkResponse(
        result=LinkResult(status_code=response.status_code),
        response=response,
    )


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
        result = await request_link_head(requester=requester, url=url)

        if result.status_code == 405:
            response = await request_link_get(requester=requester, url=url)
            result = response.result

        return link_store.add_page(
            url=url,
            info=UrlInfo(
                status_code=result.status_code,
                links=frozenset(),
            ),
        )

    link_response = await request_link_get(requester=requester, url=url)

    if link_response.result.ok():
        assert link_response.response is not None
        page_links = html.get_links(body=link_response.response.body, url=url)
    else:
        page_links = []

    return link_store.add_page(
        url=url,
        info=UrlInfo(
            status_code=link_response.result.status_code,
            links=frozenset(
                PageLink(href=origin.href, url=link) for (link, origin) in page_links
            ),
        ),
    )


async def work(
    queue: asyncio.Queue[Url],
    requester: Requester,
    link_store: LinkStore,
    start_url: Url,
):
    while True:
        url = await queue.get()
        try:
            new_urls = await investigate_url(
                requester=requester,
                link_store=link_store,
                start_url=start_url,
                url=url,
            )
            for url in new_urls:
                queue.put_nowait(url)
        finally:
            queue.task_done()


async def find_links(
    max_parallel_requests: int,
    requester: Requester,
    link_store: LinkStore,
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
    start_url: Url,
):
    requester = Requester()

    try:
        response = await requester.get(start_url)
    except RequestError as error:
        logger.error("%s", error.msg)
        exit(1)

    if not response.ok():
        logger.error("Bad response status code: %d", response.status_code)
        exit(1)

    links = html.get_links(body=response.body, url=start_url)
    first_urls = link_store.add_page(
        url=start_url,
        info=UrlInfo(
            status_code=response.status_code,
            links=frozenset(
                PageLink(href=origin.href, url=url) for (url, origin) in links
            ),
        ),
    )

    await find_links(
        max_parallel_requests=max_parallel_requests,
        requester=requester,
        link_store=link_store,
        start_url=start_url,
        first_urls=first_urls,
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
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("discolinks").setLevel(logging.DEBUG)

    logging.getLogger().setLevel(logging.WARNING)

    start_url = parse_url_arg(url)

    if start_url is None:
        logger.error("Invalid URL: %s", url)
        exit(1)

    link_store = LinkStore()

    asyncio.run(
        main_async(
            max_parallel_requests=max_parallel_requests,
            link_store=link_store,
            start_url=start_url,
        )
    )

    link_infos = link_store.get_link_infos()
    failures = [(link, info) for (link, info) in link_infos.items() if not info.ok()]
    exit_code = 1 if failures else 0

    if to_json:
        print(export.dump_json(links=link_infos))
        exit(exit_code)

    for (link, info) in failures:
        print(link)
        print(f"  status code: {info.status_code}")
        print("  origins:")
        for origin in info.origins:
            print(f"    {origin.url}: {origin.href}")

    exit(exit_code)
