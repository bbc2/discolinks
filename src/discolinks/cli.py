import json
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

import attrs
import click
import requests
from requests_html import HTMLResponse, HTMLSession

logger = logging.getLogger(__name__)


@attrs.frozen
class Link:
    url: str
    scheme: str
    netloc: str


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


def get_links(response: HTMLResponse, link: Link) -> frozenset[Link]:
    return frozenset(
        parse_html_url(url, base_link=link)
        for a in response.html.find("a")
        if (url := a.attrs.get("href")) is not None
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

    links: dict[Link, bool] = {}
    to_visit = set(get_links(response=response, link=start_link))

    while to_visit:
        link = to_visit.pop()

        try:
            response = request(session=session, link=link)
        except RequestError:
            links[link] = False
            continue

        if not response.ok:
            links[link] = False
            continue

        links[link] = True

        if link.netloc != start_link.netloc:
            continue

        new_links = get_links(response=response, link=link)
        to_visit |= new_links - links.keys()

    failures = [link for (link, success) in links.items() if not success]
    exit_code = 1 if failures else 0

    if to_json:
        print(json.dumps({link.url: success for (link, success) in links.items()}))
        exit(exit_code)

    for failed in failures:
        print(failed.url)

    exit(exit_code)
