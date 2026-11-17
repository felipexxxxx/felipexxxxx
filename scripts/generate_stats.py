"""Generate a stats card using public repository metadata, without user scopes."""
import json
import os
import re
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen


def public_repositories(owner):
    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise ValueError("Invalid GitHub username")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    repositories = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{owner}/repos?type=owner&per_page=100&page={page}"
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("Expected a list of repositories")
        repositories.extend(
            repo for repo in batch if not repo.get("private") and not repo.get("fork")
            and repo["owner"]["login"].lower() == owner.lower()
        )
        if len(batch) < 100:
            return repositories
        page += 1


def render_card(owner, repositories):
    metrics = [
        ("Original public repos", len(repositories)),
        ("Stars earned", sum(repo["stargazers_count"] for repo in repositories)),
        ("Forks received", sum(repo["forks_count"] for repo in repositories)),
    ]
    items = "".join(
        f'<text x="{x}" y="86" class="value">{value}</text>'
        f'<text x="{x}" y="111" class="label">{escape(label)}</text>'
        for x, (label, value) in zip((25, 204, 361), metrics)
    )
    description = escape("; ".join(f"{label}: {value}" for label, value in metrics))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="165" viewBox="0 0 560 165" role="img" aria-labelledby="title description">
<title id="title">{escape(owner)}: public GitHub statistics</title>
<desc id="description">{description}. Forked and private repositories are excluded.</desc>
<style>text{{font-family:Segoe UI,Ubuntu,sans-serif}}.title{{font-size:18px;font-weight:600;fill:#58a6ff}}.value{{font-size:25px;font-weight:600;fill:#f0f6fc}}.label{{font-size:12px;fill:#c3d1d9}}.note{{font-size:11px;fill:#8b949e}}</style>
<rect width="560" height="165" rx="8" fill="#0d1117"/>
<text x="25" y="34" class="title">GitHub Stats</text>
{items}
<text x="25" y="146" class="note">Public repository metadata · forked repositories excluded</text>
</svg>
'''


if __name__ == "__main__":
    owner = os.environ.get("PROFILE_OWNER", "felipexxxxx")
    repositories = public_repositories(owner)
    output = Path("dist/stats.svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_card(owner, repositories), encoding="utf-8")
    print(f"Generated {output} from {len(repositories)} original public repositories")

