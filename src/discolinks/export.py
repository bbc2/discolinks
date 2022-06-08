import json
from typing import Any, Mapping

from .core import LinkInfo, LinkOrigin, Url


def origin_to_json(origin: LinkOrigin) -> Any:
    return {
        "page": origin.url.full,
        "href": origin.href,
    }


def info_to_json(info: LinkInfo) -> Any:
    return {
        "status_code": info.status_code,
        "origins": [
            origin_to_json(origin)
            for origin in sorted(
                info.origins,
                key=lambda origin: (origin.url.full, origin.href),
            )
        ],
    }


def links_to_json(links: Mapping[Url, LinkInfo]) -> Any:
    return {url.full: info_to_json(info) for (url, info) in links.items()}


def dump_json(links: Mapping[Url, LinkInfo]) -> str:
    obj = links_to_json(links=links)
    return json.dumps(obj)
