from typing import Optional

import attrs

from .core import LinkInfo, LinkOrigin, Url


@attrs.frozen
class PageLink:
    href: str
    url: Url


@attrs.frozen
class UrlInfo:
    status_code: Optional[int]
    links: Optional[frozenset[PageLink]]

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

    def get_link_infos(self) -> dict[Url, LinkInfo]:
        """
        Return link infos for accumulated URL results.

        This should be called only at the end of the crawling.
        """

        infos: dict[Url, LinkInfo] = dict()

        for (origin_url, url_info) in self.pages.items():
            if url_info.links is None:
                continue

            for page_link in url_info.links:
                url = page_link.url
                link_info = infos.get(url)
                origin = LinkOrigin(url=origin_url, href=page_link.href)
                if link_info is None:
                    status_code = self.pages[page_link.url].status_code
                    infos[url] = LinkInfo(
                        status_code=status_code,
                        origins=frozenset([origin]),
                    )
                else:
                    infos[url] = link_info.add_origin(origin)

        return infos
