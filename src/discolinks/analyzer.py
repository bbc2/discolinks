from dataclasses import dataclass
from typing import Mapping, Sequence

from . import outcome
from .core import Url
from .url_store import UrlInfo


@dataclass(frozen=True)
class LinkResult:
    href: str
    url: Url
    results: outcome.Results

    def ok(self) -> bool:
        return self.results.ok()


@dataclass(frozen=True)
class Page:
    links: Sequence[LinkResult]


def make_chain(
    url_infos: Mapping[Url, UrlInfo],
    start_url: Url,
) -> Sequence[outcome.Result]:
    """
    Build and return a redirect chain of URL results.

    Starting with a given URL, this follows redirects to determine the path leading to a
    web page, a connection error or a cancellation.
    """

    url = start_url
    chain: list[outcome.Result] = []

    while True:
        info = url_infos.get(url)

        if info is None:
            chain.append(outcome.Unknown())
            break

        result = info.result
        chain.append(result)
        redirect_url = result.redirect_url()

        if redirect_url is None:
            break
        else:
            url = redirect_url

    return chain


@dataclass
class Stats:
    ok: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        return self.ok + self.failed

    def add(self, ok: bool) -> None:
        if ok:
            self.ok += 1
        else:
            self.failed += 1


@dataclass(frozen=True)
class Analysis:
    stats: Stats
    pages: Mapping[Url, Page]

    def ok(self) -> bool:
        return self.stats.failed == 0


def analyze(url_infos: Mapping[Url, UrlInfo]) -> Analysis:
    """
    Analyze URL data obtained from web scraping.
    """

    pages = {}
    stats = Stats()

    for url, info in url_infos.items():
        if info.links is None:
            continue

        links = []

        for link in info.links:
            result = LinkResult(
                href=link.href,
                url=link.url,
                results=outcome.Results(
                    chain=make_chain(url_infos=url_infos, start_url=link.url)
                ),
            )
            stats.add(ok=result.ok())
            links.append(result)

        pages[url] = Page(links=links)

    return Analysis(pages=pages, stats=stats)
