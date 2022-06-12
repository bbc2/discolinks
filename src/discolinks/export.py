import json
from typing import Any, Mapping

from .analyzer import Destination, LinkResult, Page
from .core import Url


def destination_to_json(destination: Destination) -> Any:
    return {
        "url": destination.url.full,
        "status_code": destination.status_code,
    }


def link_to_json(link: LinkResult) -> Any:
    return {
        "href": link.href,
        "destination": destination_to_json(link.destination),
    }


def page_to_json(page: Page) -> Any:
    return {
        "links": [link_to_json(link) for link in page.links],
    }


def pages_to_json(pages: Mapping[Url, Page]) -> Any:
    return {url.full: page_to_json(page) for (url, page) in pages.items()}


def dump_json(pages: Mapping[Url, Page]) -> str:
    obj = pages_to_json(pages=pages)
    return json.dumps(obj)
