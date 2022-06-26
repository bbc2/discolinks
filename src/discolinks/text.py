from typing import Mapping

import attrs

from . import analyzer, outcome
from .core import Url


@attrs.frozen
class Converter(outcome.Converter[str]):
    def convert_page(self, page: outcome.Page) -> str:
        return str(page.code)

    def convert_redirect(self, redirect: outcome.Redirect) -> str:
        return str(redirect.code)

    def convert_request_error(self, error: outcome.RequestError) -> str:
        return str(error.msg)


def print_results(pages: Mapping[Url, analyzer.Page]) -> None:
    for (url, info) in pages.items():
        bad_links = [link for link in info.links if not link.ok()]

        if not bad_links:
            continue

        print(f"{url}")

        for link in bad_links:
            items = link.results.convert_with(Converter())
            results = " → ".join(items)
            print(f"  - {link.href}: {results}")
