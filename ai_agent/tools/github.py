"""
Tool for github.request action
Supports basic GitHub REST API requests for repo info, issues, PRs, file contents, search, etc.
"""
import os
import base64
import requests
from typing import Optional, Dict, Any


GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com")


def _get_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_request(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Perform a GitHub API request.

    Inputs:
    - method: GET/POST/PUT/PATCH/DELETE
    - path: API path like "/repos/{owner}/{repo}", must start with '/'
    - params: query parameters
    - data: JSON body for non-GET methods
    """
    if not path.startswith("/"):
        return {"error": "path must start with '/'"}

    url = f"{GITHUB_API_BASE}{path}"
    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            headers=_get_headers(),
            params=params,
            json=data if method.upper() != "GET" else None,
            timeout=30,
        )
        status = resp.status_code
        # Handle content
        try:
            payload = resp.json()
        except Exception:
            payload = {"text": resp.text}

        # Special handling for content API base64
        if (
            status == 200
            and isinstance(payload, dict)
            and payload.get("encoding") == "base64"
            and "content" in payload
        ):
            try:
                decoded = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
                payload["decoded_content"] = decoded
            except Exception:
                pass

        return {"status": status, "data": payload}
    except Exception as e:
        return {"error": str(e), "status": 0}


