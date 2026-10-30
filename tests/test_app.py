import pytest
from reporadar_utils import parse_repo_url


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World.git", ("octocat", "Hello-World")),
        ("github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/octocat/Hello-World/tree/main", ("octocat", "Hello-World")),
    ],
)
def test_parse_repo_url_valid(url, expected):
    assert parse_repo_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://example.com/octocat/Hello-World",
        "https://github.com/octocat",
    ],
)
def test_parse_repo_url_invalid(url):
    with pytest.raises(ValueError):
        parse_repo_url(url)
