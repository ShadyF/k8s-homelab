#!/usr/bin/env python3
"""Fetch open pull request upgrade inventory from GitHub without gh."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_ROOT = "https://api.github.com"
DEFAULT_OWNER = "ShadyF"
DEFAULT_REPO = "k8s-homelab"


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "k8s-homelab-pr-upgrade-review-skill",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def request_json(url: str) -> tuple[Any, dict[str, str]]:
    request = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            headers = {key.lower(): value for key, value in response.headers.items()}
            return json.loads(body), headers
    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        if error.code == 403 and "rate limit" in message.lower():
            raise SystemExit(
                "GitHub API rate limit reached. Set GITHUB_TOKEN and rerun the helper."
            ) from error
        raise SystemExit(f"GitHub API request failed for {url}: HTTP {error.code}: {message}") from error


def next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        match = re.match(r"<([^>]+)>", section)
        if match:
            return match.group(1)
    return None


def fetch_paginated(url: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current_url: str | None = url
    while current_url:
        data, headers = request_json(current_url)
        if not isinstance(data, list):
            raise SystemExit(f"Expected list response from {current_url}")
        items.extend(data)
        current_url = next_link(headers.get("link"))
    return items


def api_url(owner: str, repo: str, path: str, query: dict[str, str] | None = None) -> str:
    encoded_path = "/".join(urllib.parse.quote(part) for part in path.strip("/").split("/"))
    url = f"{API_ROOT}/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/{encoded_path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    return url


def extract_release_links(body: str | None) -> list[str]:
    if not body:
        return []

    urls = re.findall(r"https?://[^\s)\]>\"']+", body)
    release_links: list[str] = []
    for url in urls:
        lowered = url.lower()
        if any(token in lowered for token in ("release", "changelog", "changes", "compare", "tag/")):
            if url not in release_links:
                release_links.append(url)
    return release_links


def extract_versions(title: str, body: str | None, files: list[dict[str, Any]]) -> dict[str, Any]:
    patterns = [
        r"\b(?P<old>v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?)\s+(?:to|->)\s+(?P<new>v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?)\b",
        r"\bfrom\s+(?P<old>v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?)\s+to\s+(?P<new>v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?)\b",
    ]
    candidates: list[dict[str, str]] = []
    for source, text in (("title", title), ("body", body or "")):
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                candidate = {
                    "current_version": match.group("old"),
                    "target_version": match.group("new"),
                    "source": source,
                }
                candidates.append(candidate)
                return {
                    "current_version": candidate["current_version"],
                    "target_version": candidate["target_version"],
                    "source": source,
                    "confidence": "heuristic",
                    "candidates": candidates,
                }

    for file_info in files:
        patch = file_info.get("patch") or ""
        removed = re.findall(
            r"^-.*?(v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?)",
            patch,
            flags=re.MULTILINE,
        )
        added = re.findall(
            r"^\+.*?(v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?)",
            patch,
            flags=re.MULTILINE,
        )
        if removed and added:
            candidates.extend(
                {
                    "current_version": old,
                    "target_version": new,
                    "source": f"patch:{file_info.get('filename')}",
                }
                for old, new in zip(removed, added)
            )
            first = candidates[0]
            return {
                "current_version": first["current_version"],
                "target_version": first["target_version"],
                "source": first["source"],
                "confidence": "heuristic",
                "candidates": candidates,
            }

    return {
        "current_version": None,
        "target_version": None,
        "source": "not_detected",
        "confidence": "none",
        "candidates": [],
    }


def build_inventory_item(
    pr: dict[str, Any], files: list[dict[str, Any]], commits: list[dict[str, Any]]
) -> dict[str, Any]:
    versions = extract_versions(pr.get("title", ""), pr.get("body"), files)
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "url": pr.get("html_url"),
        "body": pr.get("body"),
        "author": (pr.get("user") or {}).get("login"),
        "head_ref": (pr.get("head") or {}).get("ref"),
        "base_ref": (pr.get("base") or {}).get("ref"),
        "current_version": versions["current_version"],
        "target_version": versions["target_version"],
        "version_detection": versions,
        "release_links": extract_release_links(pr.get("body")),
        "changed_files": [file_info.get("filename") for file_info in files if file_info.get("filename")],
        "file_statuses": [
            {"filename": file_info.get("filename"), "status": file_info.get("status")}
            for file_info in files
            if file_info.get("filename")
        ],
        "files": [
            {
                "filename": file_info.get("filename"),
                "status": file_info.get("status"),
                "additions": file_info.get("additions"),
                "deletions": file_info.get("deletions"),
                "changes": file_info.get("changes"),
                "patch": file_info.get("patch"),
            }
            for file_info in files
            if file_info.get("filename")
        ],
        "commit_messages": [
            (commit.get("commit") or {}).get("message")
            for commit in commits
            if (commit.get("commit") or {}).get("message")
        ],
        "commits": [
            {
                "sha": commit.get("sha"),
                "message": (commit.get("commit") or {}).get("message"),
                "html_url": commit.get("html_url"),
            }
            for commit in commits
        ],
    }


def collect_inventory(owner: str, repo: str, state: str) -> dict[str, Any]:
    pulls_url = api_url(owner, repo, "pulls", {"state": state, "per_page": "100"})
    pulls = fetch_paginated(pulls_url)
    items: list[dict[str, Any]] = []
    for pr in pulls:
        number = pr["number"]
        files = fetch_paginated(api_url(owner, repo, f"pulls/{number}/files", {"per_page": "100"}))
        commits = fetch_paginated(api_url(owner, repo, f"pulls/{number}/commits", {"per_page": "100"}))
        items.append(build_inventory_item(pr, files, commits))
    return {"repository": f"{owner}/{repo}", "state": state, "pull_requests": items}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    parser.add_argument("--output", help="Write JSON inventory to this path instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    inventory = collect_inventory(args.owner, args.repo, args.state)
    output = json.dumps(inventory, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
            handle.write("\n")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
