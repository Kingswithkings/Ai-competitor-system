import re


def detect_trust_signals(text: str) -> dict:
    lower_text = text.lower()

    trust_terms = [
        "testimonials",
        "reviews",
        "case studies",
        "trusted by",
        "clients",
        "customer stories",
        "google reviews",
        "trustpilot",
        "verified",
        "award",
        "awards",
        "certified",
    ]

    found_terms = [term for term in trust_terms if term in lower_text]

    return {
        "has_trust_signals": len(found_terms) > 0,
        "trust_signal_terms": found_terms,
        "trust_signal_count": len(found_terms),
    }


def detect_contact_signals(text: str) -> dict:
    lower_text = text.lower()

    email_found = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
    phone_found = bool(re.search(r"(\+?\d[\d\s().-]{7,}\d)", text))

    contact_terms = ["contact us", "book a demo", "call us", "get in touch", "request a quote"]
    found_terms = [term for term in contact_terms if term in lower_text]

    return {
        "has_email": email_found,
        "has_phone": phone_found,
        "contact_cta_terms": found_terms,
        "has_contact_cta": len(found_terms) > 0,
    }


def detect_social_presence(text: str) -> dict:
    lower_text = text.lower()

    platforms = []
    for platform in ["facebook", "instagram", "linkedin", "youtube", "tiktok", "x.com", "twitter"]:
        if platform in lower_text:
            platforms.append(platform)

    return {
        "social_platforms": platforms,
        "social_count": len(platforms),
        "has_social_presence": len(platforms) > 0,
    }


def collect_review_social_signals(text: str) -> dict:
    trust = detect_trust_signals(text)
    contact = detect_contact_signals(text)
    social = detect_social_presence(text)

    return {
        **trust,
        **contact,
        **social,
    }