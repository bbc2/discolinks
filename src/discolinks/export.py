import json
from typing import Any, Mapping

from .core import Link, LinkInfo


def info_to_json(info: LinkInfo) -> Any:
    return {
        "status_code": info.status_code,
    }


def links_to_json(links: Mapping[Link, LinkInfo]) -> Any:
    return {link.url: info_to_json(info) for (link, info) in links.items()}


def dump_json(links: Mapping[Link, LinkInfo]) -> str:
    obj = links_to_json(links=links)
    return json.dumps(obj)
