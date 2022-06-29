from typing import Optional, Sequence
from urllib.parse import urldefrag, urljoin, urlparse

import bs4

from .core import Link, Url


def get_hrefs(body: str) -> Sequence[str]:
    soup = bs4.BeautifulSoup(body, features="html.parser")

    return [url for a in soup.find_all("a") if (url := a.attrs.get("href")) is not None]


def parse_href(href: str, base_url: Url) -> Optional[Url]:
    """
    Parse the value of an `href` HTML attribute into a URL.

    If the link is relative, we need the base URL to infer the absolute URL.
    """

    (href, _) = urldefrag(href)
    parsed = urlparse(href)

    if parsed.scheme not in ("", "http", "https"):
        return None

    if parsed.netloc:
        if not parsed.scheme and href.startswith("//"):
            url = f"http:{href}"
        else:
            url = href
    else:
        url = urljoin(base_url.full, href)

    return Url.from_str(url)


def get_links(body: str, url: Url) -> Sequence[Link]:
    return [
        Link(href=href, url=link_url)
        for href in get_hrefs(body)
        if (link_url := parse_href(href, base_url=url)) is not None
    ]
