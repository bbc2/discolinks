import json
from typing import Any, Mapping, Sequence

import attrs

from . import outcome
from .analyzer import Analysis, LinkResult, Page
from .core import Url


@attrs.frozen
class Converter(outcome.Converter[Any]):
    def convert_page(self, page: outcome.Page) -> Any:
        return {
            "type": "response",
            "status_code": page.code,
        }

    def convert_redirect(self, redirect: outcome.Redirect) -> Any:
        return {
            "type": "redirect",
            "status_code": redirect.code,
            "value": redirect.ref,
            "url": str(redirect.url),
        }

    def convert_request_error(self, error: outcome.RequestError) -> Any:
        return {
            "type": "request_error",
            "message": str(error.msg),
        }

    def convert_unknown(self, unknown: outcome.Unknown) -> Any:
        return {
            "type": "unknown",
        }


def results_to_json(results: outcome.Results) -> Sequence[Any]:
    return results.convert_with(Converter())


def link_to_json(link: LinkResult) -> Any:
    return {
        "href": link.href,
        "url": str(link.url),
        "results": results_to_json(link.results),
    }


def page_to_json(page: Page) -> Any:
    return {
        "links": [link_to_json(link) for link in page.links],
    }


def pages_to_json(pages: Mapping[Url, Page]) -> Any:
    return {url.full: page_to_json(page) for (url, page) in pages.items()}


def dump_json(analysis: Analysis) -> str:
    obj = pages_to_json(pages=analysis.pages)
    return json.dumps(obj)
