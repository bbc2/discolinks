import asyncio
import logging
from typing import AbstractSet, Optional, Sequence
from urllib.parse import urljoin, urlparse

import attrs
import click
import requests
from requests_html import AsyncHTMLSession, HTMLResponse

from . import export
from .core import Link, LinkOrigin
from .link_store import LinkResult, LinkStore

logger = logging.getLogger(__name__)


def parse_url_arg(url: str) -> Optional[Link]:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    parsed = urlparse(url)

    if not parsed.netloc:
        return None

    return Link(url=url, scheme=parsed.scheme, netloc=parsed.netloc)


def parse_html_url(url: str, base_link: Link) -> Link:
    parsed = urlparse(url)

    if parsed.scheme:
        scheme = parsed.scheme
    else:
        scheme = base_link.scheme

    if parsed.netloc:
        netloc = parsed.netloc
    else:
        netloc = base_link.netloc
        url = urljoin(base_link.url, url)

    return Link(url=url, scheme=scheme, netloc=netloc)


@attrs.frozen
class RequestError(Exception):
    msg: str


async def request(session: AsyncHTMLSession, link: Link) -> HTMLResponse:
    """
    Fetch an HTML page from the given link.

    Raises `RequestError` if any connection issue is encountered.
    """
    logger.debug("Requesting %s", link.url)

    try:
        response = await session.get(link.url)
    except requests.RequestException as error:
        raise RequestError(msg=str(error))

    return response


def get_links(response: HTMLResponse, link: Link) -> Sequence[tuple[Link, LinkOrigin]]:
    return [
        (parse_html_url(url, base_link=link), LinkOrigin(href=url, page=link))
        for a in response.html.find("a")
        if (url := a.attrs.get("href")) is not None
    ]


@attrs.frozen
class LinkResponse:
    result: LinkResult
    response: Optional[HTMLResponse]


async def request_link(session: AsyncHTMLSession, link: Link) -> LinkResponse:
    try:
        response = await request(session=session, link=link)
    except RequestError:
        return LinkResponse(
            result=LinkResult(status_code=None),
            response=None,
        )

    return LinkResponse(
        result=LinkResult(status_code=response.status_code),
        response=response,
    )


async def investigate_link(
    session: AsyncHTMLSession,
    link_store: LinkStore,
    start_link: Link,
    link: Link,
) -> AbstractSet[Link]:
    link_response = await request_link(session=session, link=link)
    link_store.add_result(link=link, result=link_response.result)

    if not link_response.result.ok:
        return frozenset()

    if link.netloc != start_link.netloc:
        return frozenset()

    page_links = get_links(response=link_response.response, link=link)

    new_links = link_store.add_origins(page_links)
    return new_links


async def work(
    queue: asyncio.Queue[Link],
    session: AsyncHTMLSession,
    link_store: LinkStore,
    start_link: Link,
):
    while True:
        link = await queue.get()
        try:
            new_links = await investigate_link(
                session=session,
                link_store=link_store,
                start_link=start_link,
                link=link,
            )
            for link in new_links:
                queue.put_nowait(link)
        finally:
            queue.task_done()


async def find_links(
    max_parallel_requests: int,
    session: AsyncHTMLSession,
    link_store: LinkStore,
    start_link: Link,
    start_response: HTMLResponse,
) -> None:
    queue: asyncio.Queue[Link] = asyncio.Queue()
    page_links = get_links(response=start_response, link=start_link)
    new_links = link_store.add_origins(page_links)

    for link in new_links:
        queue.put_nowait(link)

    workers: list[asyncio.Task] = []

    for _ in range(max_parallel_requests):
        worker = asyncio.create_task(
            work(
                queue=queue,
                session=session,
                link_store=link_store,
                start_link=start_link,
            ),
        )
        workers.append(worker)

    await queue.join()

    for worker in workers:
        worker.cancel()

    await asyncio.gather(*workers, return_exceptions=True)


async def main_async(
    max_parallel_requests: int,
    link_store: LinkStore,
    start_link: Link,
):
    session = AsyncHTMLSession()

    try:
        response = await request(session=session, link=start_link)
    except RequestError as error:
        logger.error("%s", error.msg)
        exit(1)

    if not response.ok:
        logger.error("Bad response status code: %d", response.status_code)
        exit(1)

    await find_links(
        max_parallel_requests=max_parallel_requests,
        session=AsyncHTMLSession(),
        link_store=link_store,
        start_link=start_link,
        start_response=response,
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
        logger.setLevel(logging.DEBUG)

    logging.getLogger().setLevel(logging.WARNING)

    start_link = parse_url_arg(url)

    if start_link is None:
        logger.error("Invalid URL: %s", url)
        exit(1)

    link_store = LinkStore()

    asyncio.run(
        main_async(
            max_parallel_requests=max_parallel_requests,
            link_store=link_store,
            start_link=start_link,
        )
    )

    link_infos = link_store.get_link_infos()
    failures = [(link, info) for (link, info) in link_infos.items() if not info.ok()]
    exit_code = 1 if failures else 0

    if to_json:
        print(export.dump_json(links=link_infos))
        exit(exit_code)

    for (link, info) in failures:
        print(link.url)
        print(f"  status code: {info.status_code}")
        print("  origins:")
        for origin in info.origins:
            print(f"    {origin.page.url}: {origin.href}")

    exit(exit_code)
