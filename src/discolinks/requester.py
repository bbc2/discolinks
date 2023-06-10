import logging
import ssl
from typing import Union

import attrs
import httpx

from . import outcome
from .core import Url
from .excluder import Excluder

logger = logging.getLogger(__name__)


def httpx_to_result(response: httpx.Response) -> outcome.Result:
    if response.next_request is not None:
        return outcome.Redirect(
            code=response.status_code,
            ref=response.headers["location"],
            url=Url.from_str(str(response.next_request.url)),
        )
    else:
        return outcome.Page(
            code=response.status_code,
            body=response.text,
        )


def httpx_to_error(error: Union[httpx.RequestError, ssl.SSLError]) -> str:
    if isinstance(error, httpx.TimeoutException):
        return "Network timeout"

    return str(error)


@attrs.frozen
class Requester:
    excluder: Excluder
    client: httpx.AsyncClient = attrs.field(init=False, factory=httpx.AsyncClient)

    async def get(self, url: Url, use_head: bool = False) -> outcome.Result:
        """
        Fetch a page from the given HTTP URL.
        """
        method = "HEAD" if use_head else "GET"

        if self.excluder.is_excluded(url):
            logger.debug("Excluded: %s", url)
            return outcome.Excluded()
        else:
            logger.debug("%s %s", method, url)

        try:
            response = await self.client.request(method=method, url=url.full)
        except (httpx.RequestError, ssl.SSLError) as error:
            msg = httpx_to_error(error)
            return outcome.RequestError(msg=msg)

        return httpx_to_result(response)
