import json
from typing import Any, Mapping

from .core import Link, LinkInfo, LinkOrigin


def origin_to_json(origin: LinkOrigin) -> Any:
    return {
        "page": origin.page.url,
        "href": origin.href,
    }


def info_to_json(info: LinkInfo) -> Any:
    return {
        "status_code": info.status_code,
        "origins": [
            origin_to_json(origin)
            for origin in sorted(
                info.origins,
                key=lambda origin: (origin.page.url, origin.href),
            )
        ],
    }


def links_to_json(links: Mapping[Link, LinkInfo]) -> Any:
    return {link.url: info_to_json(info) for (link, info) in links.items()}


def dump_json(links: Mapping[Link, LinkInfo]) -> str:
    obj = links_to_json(links=links)
    return json.dumps(obj)
