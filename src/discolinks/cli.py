import logging
from typing import Iterable, Optional, Sequence
from urllib.parse import urljoin, urlparse

import attrs
import click
import requests
from requests_html import HTMLResponse, HTMLSession

from . import export
from .core import Link, LinkInfo, LinkOrigin

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


def request(session: HTMLSession, link: Link) -> HTMLResponse:
    """
    Fetch an HTML page from the given link.

    Raises `RequestError` if any connection issue is encountered.
    """
    logger.debug("Requesting %s", link.url)

    try:
        response = session.get(link.url)
    except requests.RequestException as error:
        raise RequestError(msg=str(error))

    return response


def get_links(response: HTMLResponse, link: Link) -> Sequence[tuple[Link, LinkOrigin]]:
    return [
        (parse_html_url(url, base_link=link), LinkOrigin(href=url, page=link))
        for a in response.html.find("a")
        if (url := a.attrs.get("href")) is not None
    ]


def update_link_origins(
    links: dict[Link, set[LinkOrigin]],
    new_links: Iterable[tuple[Link, LinkOrigin]],
) -> None:
    for (link, origin) in new_links:
        existing_origins = links.get(link)
        if existing_origins is None:
            links[link] = set([origin])
        else:
            links[link].add(origin)


@attrs.frozen
class LinkResult:
    status_code: Optional[int]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)


@attrs.frozen
class LinkResponse:
    result: LinkResult
    response: Optional[HTMLResponse]


def request_link(session: HTMLSession, link: Link) -> LinkResponse:
    try:
        response = request(session=session, link=link)
    except RequestError:
        return LinkResponse(
            result=LinkResult(status_code=None),
            response=None,
        )

    return LinkResponse(
        result=LinkResult(status_code=response.status_code),
        response=response,
    )


def investigate_link(
    session: HTMLSession,
    link_results: dict[Link, LinkResult],
    link_origins: dict[Link, set[LinkOrigin]],
    to_visit: set[Link],
    start_link: Link,
    link: Link,
):
    link_response = request_link(session=session, link=link)
    link_results[link] = link_response.result

    if not link_response.result.ok:
        return

    if link.netloc != start_link.netloc:
        return

    page_links = get_links(response=link_response.response, link=link)
    update_link_origins(link_origins, page_links)
    to_visit |= set([link for (link, _) in page_links]) - link_results.keys()


def find_links(
    session: HTMLSession,
    link_results: dict[Link, LinkResult],
    link_origins: dict[Link, set[LinkOrigin]],
    start_link: Link,
    start_response: HTMLResponse,
) -> None:
    page_links = get_links(response=start_response, link=start_link)
    update_link_origins(link_origins, page_links)
    to_visit = set([link for (link, _) in page_links])

    while to_visit:
        link = to_visit.pop()
        investigate_link(
            session=session,
            link_results=link_results,
            link_origins=link_origins,
            to_visit=to_visit,
            start_link=start_link,
            link=link,
        )


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    help="Increase verbosity to show debug messages.",
)
@click.option(
    "--json",
    "to_json",
    is_flag=True,
    help="Export results as JSON to the standard output.",
)
@click.option("--url", required=True, help="URL where crawling will start.")
def main(verbose: bool, to_json: bool, url: str) -> None:
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    logging.getLogger().setLevel(logging.WARNING)

    session = HTMLSession()
    start_link = parse_url_arg(url)

    if start_link is None:
        logger.error("Invalid URL: %s", url)
        exit(1)

    try:
        response = request(session=session, link=start_link)
    except RequestError as error:
        logger.error("%s", error.msg)
        exit(1)

    if not response.ok:
        logger.error("Bad response status code: %d", response.status_code)
        exit(1)

    link_results: dict[Link, LinkResult] = {}
    link_origins: dict[Link, set[LinkOrigin]] = {}

    find_links(
        session=session,
        link_results=link_results,
        link_origins=link_origins,
        start_link=start_link,
        start_response=response,
    )

    link_infos = {
        link: LinkInfo(
            status_code=result.status_code,
            origins=frozenset(link_origins[link]),
        )
        for (link, result) in link_results.items()
    }

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
