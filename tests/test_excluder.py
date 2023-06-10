import pytest

from discolinks.core import Url
from discolinks.excluder import Excluder, ExcluderRegexError


def test_excluder_from_regexes_error():
    with pytest.raises(ExcluderRegexError) as error:
        Excluder.from_regexes("(")

    assert error.value.regex == "("
    assert error.value.msg == "missing ), unterminated subpattern at position 0"


@pytest.mark.parametrize(
    "regexes,url,expected",
    [
        ([], Url.from_str("https://foo"), False),
        (["a"], Url.from_str("https://foo"), False),
        (["f"], Url.from_str("https://foo"), True),
        (["^f"], Url.from_str("https://foo"), False),
        (["^h"], Url.from_str("https://foo"), True),
        (["a", "b"], Url.from_str("https://foo"), False),
        (["a", "f"], Url.from_str("https://foo"), True),
    ],
)
def test_excluder_combined(regexes: str, url: Url, expected: bool):
    result = Excluder.from_regexes(regexes).is_excluded(url)

    assert result is expected
