import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

from app.scraper import normalize_url, get_domain


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

EXCLUDED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "trustpilot.com",
    "tripadvisor.com",
    "wikipedia.org",
    "crunchbase.com",
    "indeed.com",
    "glassdoor.com",
}

EXCLUDED_KEYWORDS = [
    "directory",
    "listing",
    "review",
    "jobs",
    "career",
]


def is_excluded(url: str, target_domain: str = "") -> bool:
    domain = get_domain(url)

    if target_domain and domain == target_domain:
        return True

    if any(domain.endswith(blocked) for blocked in EXCLUDED_DOMAINS):
        return True

    lower_url = url.lower()
    if any(keyword in lower_url for keyword in EXCLUDED_KEYWORDS):
        return True

    return False


def search_duckduckgo(query: str, max_results: int = 10) -> list:
    search_url = "https://html.duckduckgo.com/html/"
    response = requests.post(
        search_url,
        data={"q": query},
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    results = []

    for a_tag in soup.select("a.result__a"):
        href = a_tag.get("href")
        title = a_tag.get_text(" ", strip=True)

        if not href:
            continue

        href = unquote(href)

        if href.startswith("//"):
            href = f"https:{href}"

        results.append({
            "title": title,
            "url": href
        })

        if len(results) >= max_results:
            break

    return results


def discover_competitor_candidates(
    business_name: str,
    industry: str,
    target_website: str,
    location: str | None = None,
    max_results: int = 10
) -> list:
    target_domain = get_domain(target_website)
    queries = [
        f"{business_name} competitors {industry}",
        f"best {industry} companies like {business_name}",
        f"{industry} businesses similar to {business_name}",
    ]

    if location:
        queries.append(f"{industry} companies in {location}")

    seen_domains = set()
    candidates = []

    for query in queries:
        try:
            results = search_duckduckgo(query, max_results=max_results)
        except Exception:
            continue

        for item in results:
            url = item["url"]

            if is_excluded(url, target_domain=target_domain):
                continue

            domain = get_domain(url)
            if domain in seen_domains:
                continue

            seen_domains.add(domain)
            candidates.append({
                "name": item["title"],
                "website": normalize_url(url)
            })

    return candidates[:10]
