import re
from typing import Sequence

import attrs

from .core import Url


@attrs.frozen
class ExcluderRegexError(Exception):
    regex: str
    msg: str


def parse_regex(regex: str) -> re.Pattern:
    try:
        return re.compile(regex)
    except re.error as error:
        raise ExcluderRegexError(regex=regex, msg=str(error))


@attrs.frozen
class Excluder:
    """
    Preprocessed engine excluding certain URLs
    """

    patterns: Sequence[re.Pattern]

    @classmethod
    def from_regexes(cls, regexes: Sequence[str]) -> "Excluder":
        """
        Parse regular expressions to be used as exclusion patterns.

        Raises `ExcluderRegexError` if any of the regexes can't be parsed.
        """
        patterns = [parse_regex(regex) for regex in regexes]
        return cls(patterns=patterns)

    def is_excluded(self, url: Url) -> bool:
        return any(re.search(pattern, str(url)) for pattern in self.patterns)
