from typing import AbstractSet, Iterable, Optional

import attrs

from .core import Link, LinkInfo, LinkOrigin


@attrs.frozen
class LinkResult:
    status_code: Optional[int]

    def ok(self):
        return self.status_code is not None and not (400 <= self.status_code < 600)


@attrs.define
class LinkState:
    result: Optional[LinkResult]
    origins: set[LinkOrigin] = attrs.field(factory=set)

    def set_result(self, result: LinkResult) -> None:
        assert self.result is None
        self.result = result

    def get_result(self) -> LinkResult:
        assert self.result is not None
        return self.result


@attrs.frozen
class LinkStore:
    links: dict[Link, LinkState] = attrs.field(init=False, factory=dict)

    def add_result(self, link: Link, result: LinkResult) -> None:
        """
        Add request result for a given link.

        Only new links can be added. Existing links cannot be updated.
        """
        state = self.links.get(link)
        if state is None:
            self.links[link] = LinkState(result=result)
        else:
            state.set_result(result)

    def add_origin(self, link: Link, origin: LinkOrigin) -> bool:
        state = self.links.get(link)
        if state is None:
            self.links[link] = LinkState(result=None, origins=set([origin]))
            return True
        else:
            state.origins.add(origin)
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

    def get_link_infos(self) -> dict[Link, LinkInfo]:
        """
        Return link infos for accumulated link results and origins.

        This should be called only at the end of the crawling.
        """

        return {
            link: LinkInfo(
                status_code=state.get_result().status_code,
                origins=frozenset(state.origins),
            )
            for (link, state) in self.links.items()
        }
