from urllib.parse import urlparse
import re


def parse_repo_url(repo_url: str):
    """Return (owner, repo) from common GitHub repository URL formats."""
    value = repo_url.strip()
    if not value:
        raise ValueError("Enter a GitHub repository URL.")

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Please enter a URL from github.com.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("URL must include both the owner and repository name.")

    owner, repo = parts[0], parts[1]
    repo = re.sub(r"\.git$", "", repo)
    if not owner or not repo:
        raise ValueError("Could not read the owner and repository name.")
    return owner, repo

