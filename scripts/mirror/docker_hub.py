import json
from urllib.request import Request, urlopen


def fetch_tags(namespace: str, repository: str) -> dict:
    url = (
        f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/"
        f"{repository}/tags?page_size=100"
    )
    results = []

    while url:
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request) as response:
            payload = json.load(response)
        results.extend(payload.get("results", []))
        url = payload.get("next")

    return {"results": results}
