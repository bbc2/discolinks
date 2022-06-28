from typing import Optional, Sequence

import attrs

from . import html, outcome
from .core import Link, Url


@attrs.frozen
class LinkExtractor(outcome.Converter[Optional[Sequence[Link]]]):
    url: Url

    def convert_redirect(self, redirect: outcome.Redirect) -> None:
        return None

    def convert_page(self, page: outcome.Page) -> Sequence[Link]:
        return html.get_links(body=page.body, url=self.url)

    def convert_request_error(self, error: outcome.RequestError) -> None:
        return None

    def convert_unknown(self, unknown: outcome.Unknown) -> None:
        return None


def get_links(url: Url, result: outcome.Result) -> Optional[Sequence[Link]]:
    converter = LinkExtractor(url=url)
    return result.convert_with(converter)
