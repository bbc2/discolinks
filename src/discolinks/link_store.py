from typing import Mapping, Optional, Sequence

import attrs

from .core import Link, Url


@attrs.frozen
class UrlInfo:
    status_code: Optional[int]
    links: Optional[Sequence[Link]]

    def link_urls(self) -> frozenset[Url]:
        if self.links is None:
            return frozenset()
        else:
            return frozenset(link.url for link in self.links)


@attrs.frozen
class LinkStore:
    pages: dict[Url, UrlInfo] = attrs.field(init=False, factory=dict)
    seen_urls: set[Url] = attrs.field(init=False, factory=set)

    def add_page(self, url: Url, info: UrlInfo) -> frozenset[Url]:
        """
        Store page information for a given URL and return new URLs.

        This can only be called once for each URL and each discovered URL is only returned
        once.
        """

        assert url not in self.pages, f"URL already stored: {url}"
        self.pages[url] = info
        self.seen_urls.add(url)
        new_urls = info.link_urls() - self.seen_urls
        self.seen_urls.update(new_urls)
        return new_urls

    def get_url_infos(self) -> Mapping[Url, UrlInfo]:
        return self.pages
