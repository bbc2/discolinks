from abc import ABC, abstractmethod
from typing import Generic, Optional, Sequence, TypeVar

import attrs

from .core import Url

Out = TypeVar("Out")


@attrs.frozen
class Result(ABC):
    @abstractmethod
    def ok(self) -> bool:
        pass

    @abstractmethod
    def status_code(self) -> Optional[int]:
        pass

    @abstractmethod
    def redirect_url(self) -> Optional[Url]:
        pass

    @abstractmethod
    def error_msg(self) -> Optional[str]:
        pass

    @abstractmethod
    def convert_with(self, converter: "Converter[Out]") -> Out:
        pass


@attrs.frozen
class Redirect(Result):
    code: int
    ref: str
    url: Url

    def ok(self) -> bool:
        return True

    def status_code(self) -> Optional[int]:
        return self.code

    def redirect_url(self) -> Optional[Url]:
        return self.url

    def error_msg(self) -> Optional[str]:
        return None

    def convert_with(self, converter: "Converter[Out]") -> Out:
        return converter.convert_redirect(self)


@attrs.frozen
class Page(Result):
    code: int
    body: str

    def ok(self) -> bool:
        return not (400 <= self.code < 600)

    def status_code(self) -> Optional[int]:
        return self.code

    def redirect_url(self) -> Optional[Url]:
        return None

    def error_msg(self) -> Optional[str]:
        return None

    def convert_with(self, converter: "Converter[Out]") -> Out:
        return converter.convert_page(self)


@attrs.frozen
class RequestError(Result):
    msg: str

    def ok(self) -> bool:
        return False

    def status_code(self) -> Optional[int]:
        return None

    def redirect_url(self) -> Optional[Url]:
        return None

    def error_msg(self) -> Optional[str]:
        return self.msg

    def convert_with(self, converter: "Converter[Out]") -> Out:
        return converter.convert_request_error(self)


@attrs.frozen
class Unknown(Result):
    def ok(self) -> bool:
        # It's considered OK because the underlying error will be reported by another
        # mechanism.
        return True

    def status_code(self) -> Optional[int]:
        return None

    def redirect_url(self) -> Optional[Url]:
        return None

    def error_msg(self) -> Optional[str]:
        return None

    def convert_with(self, converter: "Converter[Out]") -> Out:
        return converter.convert_unknown(self)


@attrs.frozen
class Results:
    chain: Sequence[Result]

    def ok(self) -> bool:
        final = self.chain[-1]
        return final.ok()

    def convert_with(self, converter: "Converter[Out]") -> Sequence[Out]:
        return tuple(item.convert_with(converter) for item in self.chain)


class Converter(ABC, Generic[Out]):
    @abstractmethod
    def convert_redirect(self, redirect: Redirect) -> Out:
        pass

    @abstractmethod
    def convert_page(self, page: Page) -> Out:
        pass

    @abstractmethod
    def convert_request_error(self, error: RequestError) -> Out:
        pass

    @abstractmethod
    def convert_unknown(self, unknown: Unknown) -> Out:
        pass
