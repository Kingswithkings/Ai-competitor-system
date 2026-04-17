import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def get_domain(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return parsed.netloc.replace("www.", "").lower()


def fetch_html(url: str, timeout: int = 12) -> str:
    url = normalize_url(url)
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_visible_text(html: str, max_chars: int = 5000) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "img", "footer"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())
    return text[:max_chars]


def get_website_text(url: str) -> str:
    try:
        html = fetch_html(url)
        return extract_visible_text(html)
    except Exception as e:
        return f"ERROR: Failed to fetch {url}. Reason: {str(e)}"