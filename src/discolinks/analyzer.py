from typing import Mapping, Optional, Sequence

import attrs

from .core import Url
from .link_store import UrlInfo


@attrs.frozen
class Destination:
    url: Url
    status_code: Optional[int]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)


@attrs.frozen
class LinkResult:
    href: str
    destination: Destination

    def ok(self):
        return self.destination.ok()


@attrs.frozen
class Page:
    links: Sequence[LinkResult]


def analyze(url_infos: Mapping[Url, UrlInfo]) -> Mapping[Url, Page]:
    return {
        url: Page(
            links=tuple(
                LinkResult(
                    href=link.href,
                    destination=Destination(
                        url=link.url,
                        status_code=url_infos[link.url].status_code,
                    ),
                )
                for link in info.links
            )
        )
        for (url, info) in url_infos.items()
        if info.links is not None
    }
