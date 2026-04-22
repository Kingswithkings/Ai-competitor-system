import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


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


def fetch_html(url: str, timeout: int = 15) -> str:
    url = normalize_url(url)
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_visible_text(html: str, max_chars: int = 6000) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "img", "footer"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = clean_text(text)
    return text[:max_chars]


def get_website_text(url: str) -> str:
    try:
        html = fetch_html(url)
        return extract_visible_text(html)
    except Exception as e:
        return f"ERROR: Failed to fetch {url}. Reason: {str(e)}"


def extract_internal_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    base_domain = get_domain(base_url)
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(base_url, href)

        if get_domain(full_url) == base_domain:
            links.append(full_url)

    seen = []
    for link in links:
        if link not in seen:
            seen.append(link)

    return seen


def find_priority_pages(base_url: str, html: str) -> list[str]:
    internal_links = extract_internal_links(base_url, html)
    keywords = ["about", "service", "services", "product", "products", "contact", "solutions"]

    selected = [normalize_url(base_url)]

    for link in internal_links:
        lower_link = link.lower()
        if any(keyword in lower_link for keyword in keywords):
            if link not in selected:
                selected.append(link)

    return selected[:5]


def get_multi_page_text(url: str, max_pages: int = 5, max_chars_per_page: int = 3000) -> dict:
    try:
        html = fetch_html(url)
        pages = find_priority_pages(url, html)[:max_pages]

        collected = []
        for page_url in pages:
            try:
                page_html = fetch_html(page_url)
                page_text = extract_visible_text(page_html, max_chars=max_chars_per_page)
                collected.append({
                    "url": page_url,
                    "text": page_text
                })
            except Exception as e:
                collected.append({
                    "url": page_url,
                    "text": f"ERROR: Failed to fetch page. Reason: {str(e)}"
                })

        combined_text = "\n\n".join(
            f"PAGE: {item['url']}\n{item['text']}" for item in collected
        )

        return {
            "pages": collected,
            "combined_text": combined_text[:12000]
        }

    except Exception as e:
        return {
            "pages": [],
            "combined_text": f"ERROR: Failed to fetch site. Reason: {str(e)}"
        }
