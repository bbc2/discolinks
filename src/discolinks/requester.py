import logging
import ssl

import attrs
import httpx

from . import outcome
from .core import Url

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


@attrs.frozen
class Requester:
    client: httpx.AsyncClient = attrs.field(init=False, factory=httpx.AsyncClient)

    async def get(self, url: Url, use_head: bool = False) -> outcome.Result:
        """
        Fetch a page from the given HTTP URL.
        """
        method = "HEAD" if use_head else "GET"
        logger.debug("%s %s", method, url)

        try:
            response = await self.client.request(method=method, url=url.full)
        except (httpx.RequestError, ssl.SSLError) as error:
            return outcome.RequestError(msg=str(error))

        return httpx_to_result(response)
