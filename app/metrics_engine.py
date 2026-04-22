from app.review_collector import collect_review_social_signals


def compute_metrics(text: str) -> dict:
    lower_text = text.lower()

    has_services = any(term in lower_text for term in [
        "services", "solutions", "products", "what we do", "our offering"
    ])

    has_cta = any(term in lower_text for term in [
        "contact us", "book a demo", "get started", "request a quote", "sign up", "buy now"
    ])

    has_ai_signals = any(term in lower_text for term in [
        "ai", "artificial intelligence", "chatbot", "automation", "automated", "self-service",
        "smart ordering", "booking engine"
    ])

    has_clear_value_prop = any(term in lower_text for term in [
        "we help", "we provide", "we offer", "our mission", "for businesses", "for teams"
    ])

    review_social = collect_review_social_signals(text)

    return {
        "has_services": has_services,
        "has_cta": has_cta,
        "has_ai_signals": has_ai_signals,
        "has_clear_value_prop": has_clear_value_prop,
        **review_social,
    }