from typing import Mapping, Sequence

import attrs

from . import outcome
from .core import Url
from .link_store import UrlInfo


@attrs.frozen
class LinkResult:
    href: str
    url: Url
    results: outcome.Results

    def ok(self) -> bool:
        return self.results.ok()


@attrs.frozen
class Page:
    links: Sequence[LinkResult]


def make_chain(url_infos: Mapping[Url, UrlInfo], start_url: Url):
    url = start_url
    chain: list[outcome.Result] = []

    while True:
        result = url_infos[url].result
        chain.append(result)
        redirect_url = result.redirect_url()
        if redirect_url is None:
            break
        else:
            url = redirect_url

    return chain


def analyze(url_infos: Mapping[Url, UrlInfo]) -> Mapping[Url, Page]:
    return {
        url: Page(
            links=tuple(
                LinkResult(
                    href=link.href,
                    url=link.url,
                    results=outcome.Results(
                        chain=make_chain(url_infos=url_infos, start_url=link.url)
                    ),
                )
                for link in info.links
            )
        )
        for (url, info) in url_infos.items()
        if info.links is not None
    }
