from typing import Sequence
from urllib.parse import urldefrag, urljoin, urlparse

import bs4

from .core import Link, LinkOrigin


def get_hrefs(body: str) -> Sequence[str]:
    soup = bs4.BeautifulSoup(body, features="html.parser")

    return [
        url
        for a in soup.find_all("a")
        if (url := a.attrs.get("href")) is not None and not url.startswith("mailto:")
    ]


def parse_href(href: str, base_link: Link) -> Link:
    """
    Parse the value of an `href` HTML attribute into a URL.

    If the link is relative, we need the base URL to infer the absolute URL.
    """

    (href, _) = urldefrag(href)
    parsed = urlparse(href)

    if parsed.scheme:
        scheme = parsed.scheme
    else:
        scheme = base_link.scheme

    if parsed.netloc:
        netloc = parsed.netloc
        url = href
    else:
        netloc = base_link.netloc
        url = urljoin(base_link.url, href)

    return Link(url=url, scheme=scheme, netloc=netloc)


def get_links(body: str, link: Link) -> Sequence[tuple[Link, LinkOrigin]]:
    return [
        (parse_href(href, base_link=link), LinkOrigin(href=href, page=link))
        for href in get_hrefs(body)
    ]
