from typing import Optional

import attrs

from .core import Link, LinkInfo, LinkOrigin


@attrs.frozen
class PageLink:
    href: str
    url: Link


@attrs.frozen
class UrlInfo:
    status_code: Optional[int]
    links: Optional[frozenset[PageLink]]

    def link_urls(self) -> frozenset[Link]:
        if self.links is None:
            return frozenset()
        else:
            return frozenset(link.url for link in self.links)


@attrs.frozen
class LinkStore:
    pages: dict[Link, UrlInfo] = attrs.field(init=False, factory=dict)
    seen_urls: set[Link] = attrs.field(init=False, factory=set)

    def add_page(self, link: Link, info: UrlInfo) -> frozenset[Link]:
        """
        Store page information for a given URL and return new URLs.

        This can only be called once for each URL and each discovered URL is only returned
        once.
        """

        assert link not in self.pages, f"URL already stored: {link.url}"
        self.pages[link] = info
        self.seen_urls.add(link)
        new_urls = info.link_urls() - self.seen_urls
        self.seen_urls.update(new_urls)
        return new_urls

    def get_link_infos(self) -> dict[Link, LinkInfo]:
        """
        Return link infos for accumulated URL results.

        This should be called only at the end of the crawling.
        """

        infos: dict[Link, LinkInfo] = dict()

        for (url, url_info) in self.pages.items():
            if url_info.links is None:
                continue

            origin_url = url

            for page_link in url_info.links:
                link = page_link.url
                link_info = infos.get(link)
                origin = LinkOrigin(page=origin_url, href=page_link.href)
                if link_info is None:
                    status_code = self.pages[page_link.url].status_code
                    infos[link] = LinkInfo(
                        status_code=status_code,
                        origins=frozenset([origin]),
                    )
                else:
                    infos[link] = link_info.add_origin(origin)

        return infos
