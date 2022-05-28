from typing import AbstractSet, Iterable, Optional

import attrs

from .core import Link, LinkInfo, LinkOrigin


@attrs.frozen
class LinkResult:
    status_code: Optional[int]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)


@attrs.frozen
class LinkStore:
    results: dict[Link, LinkResult] = attrs.field(init=False, default={})
    origins: dict[Link, set[LinkOrigin]] = attrs.field(init=False, default={})

    def add_result(self, link: Link, result: LinkResult) -> None:
        """
        Add request result for a given link.

        Only new links can be added. Existing links cannot be updated.
        """
        assert link not in self.results

        self.results[link] = result

    def add_origin(self, link: Link, origin: LinkOrigin) -> bool:
        existing_origins = self.origins.get(link)
        if existing_origins is None:
            self.origins[link] = set([origin])
            return True
        else:
            self.origins[link].add(origin)
            return False

    def add_origins(
        self, links: Iterable[tuple[Link, LinkOrigin]]
    ) -> AbstractSet[Link]:
        """
        Add HTTP/HTML origins to links fetched earlier and return new links.

        Each new origin is added to the set of origins stored for each links. If a link is
        new (no origin was known for that link), it will be part of the returned set of
        links.
        """
        new_links = set()

        for (link, origin) in links:
            if self.add_origin(link=link, origin=origin):
                new_links.add(link)

        return new_links

    def get_known_links(self) -> AbstractSet[Link]:
        return self.results.keys()

    def get_link_infos(self) -> dict[Link, LinkInfo]:
        """
        Return link infos for accumulated link results and origins.

        This should be called only at the end of the crawling.
        """

        return {
            link: LinkInfo(
                status_code=result.status_code,
                origins=frozenset(self.origins[link]),
            )
            for (link, result) in self.results.items()
        }
