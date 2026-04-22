import os
import json
from openai import OpenAI

from app.config import get_required_env
from app.scraper import normalize_url, get_multi_page_text
from app.search_engine import discover_competitor_candidates
from app.metrics_engine import compute_metrics
from app.scoring import enrich_competitor_scores, compute_market_summary


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=get_required_env("OPENAI_API_KEY"))


def extract_business_identity(
    client: OpenAI,
    website: str,
    industry: str,
    location: str | None,
    business_text: str,
) -> dict:
    prompt = f"""
You are identifying a business from its website.

Website: {website}
Industry: {industry}
Location: {location or "Not provided"}

Website text:
\"\"\"
{business_text[:5000]}
\"\"\"

Return ONLY valid JSON:
{{
  "business_name": "",
  "summary": "",
  "core_offer": ""
}}

No markdown.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    return json.loads(response.choices[0].message.content.strip())


def select_best_competitors(
    client: OpenAI,
    business_name: str,
    industry: str,
    location: str | None,
    business_text: str,
    candidates: list
) -> list:
    prompt = f"""
You are selecting the most likely real competitors for a business.

Business name: {business_name}
Industry: {industry}
Location: {location or "Not provided"}

Business website summary text:
\"\"\"
{business_text[:3500]}
\"\"\"

Candidate competitor websites:
{json.dumps(candidates, indent=2)}

Select the 3 best competitors.

Return ONLY valid JSON:
{{
  "competitors": [
    {{
      "name": "",
      "website": ""
    }}
  ]
}}

Rules:
- Return exactly 3 if possible
- Prefer real competitors selling similar services or products
- Prefer location relevance when location is available
- Exclude directories, media, review sites, and social profiles
- No markdown
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    data = json.loads(response.choices[0].message.content.strip())
    return data.get("competitors", [])


def compare_business_to_competitors(
    client: OpenAI,
    website: str,
    industry: str,
    location: str | None,
    business_text: str,
    target_metrics: dict,
    competitors: list
) -> dict:
    competitor_data = []

    for comp in competitors:
        comp_name = comp.get("name", "Unknown Competitor")
        comp_website = comp.get("website", "")
        comp_site = get_multi_page_text(comp_website) if comp_website else {"pages": [], "combined_text": "No website provided."}
        comp_metrics = compute_metrics(comp_site["combined_text"])

        competitor_data.append({
            "name": comp_name,
            "website": comp_website,
            "text": comp_site["combined_text"][:7000],
            "metrics": comp_metrics,
        })

    prompt = f"""
You are an AI business audit assistant.

Target business website: {website}
Industry: {industry}
Location: {location or "Not provided"}

Target business website text:
\"\"\"
{business_text[:7000]}
\"\"\"

Target business metrics:
{json.dumps(target_metrics, indent=2)}

Competitor website data:
{json.dumps(competitor_data, indent=2)}

Return ONLY valid JSON in this structure:
{{
  "competitors": [
    {{
      "name": "",
      "website": "",
      "presence": 0,
      "engagement": 0,
      "automation": 0,
      "strength": ""
    }}
  ],
  "insights": [
    ""
  ],
  "recommendations": [
    ""
  ],
  "ai_tool_recommendations": [
    {{
      "business_need": "",
      "tool_category": "",
      "suggested_tools": ["", ""],
      "reason": "",
      "priority": "",
      "implementation_type": ""
    }}
  ]
}}

Scoring guidance:
- presence = website clarity, professionalism, trust signals, visibility of offer
- engagement = CTA quality, contact flow, trust indicators, conversion signals
- automation = evidence of chatbot, booking, self-service, workflow automation, AI features

AI tool recommendation rules:
- Match the recommendation to a business need or gap
- Use priorities: High, Medium, Low
- Use implementation_type values: off_the_shelf or custom_build
- Suggested tool categories can include:
  customer_support, crm_sales, marketing_content, scheduling_admin,
  ecommerce_ordering, workflow_automation, knowledge_management
- Recommend 1 to 3 tools per business need
- Be practical for SMEs
- Use custom_build where a tailored workflow gives a real advantage

Rules:
- Scores must be 1 to 10
- Ground reasoning in visible website evidence and supplied metrics
- Be conservative where evidence is weak
- No markdown
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    return json.loads(response.choices[0].message.content.strip())


def analyze_business(
    website: str,
    industry: str,
    business_name: str | None = None,
    location: str | None = None
) -> dict:
    client = get_openai_client()
    website = normalize_url(website)
    target_site = get_multi_page_text(website)
    business_text = target_site["combined_text"]
    target_metrics = compute_metrics(business_text)

    identity = extract_business_identity(
        client=client,
        website=website,
        industry=industry,
        location=location,
        business_text=business_text,
    )

    resolved_business_name = business_name or identity.get("business_name", "Unknown Business")

    candidates = discover_competitor_candidates(
        business_name=resolved_business_name,
        industry=industry,
        target_website=website,
        location=location,
        max_results=8,
    )

    competitors = select_best_competitors(
        client=client,
        business_name=resolved_business_name,
        industry=industry,
        location=location,
        business_text=business_text,
        candidates=candidates,
    )

    result = compare_business_to_competitors(
        client=client,
        website=website,
        industry=industry,
        location=location,
        business_text=business_text,
        target_metrics=target_metrics,
        competitors=competitors,
    )

    scored_competitors = enrich_competitor_scores(result.get("competitors", []))
    market_summary = compute_market_summary(scored_competitors)

    result["competitors"] = scored_competitors
    result["market_summary"] = market_summary
    result["target_metrics"] = target_metrics
    result["candidate_competitors"] = candidates
    result["collected_pages"] = target_site["pages"]

    if "ai_tool_recommendations" not in result:
        result["ai_tool_recommendations"] = []

    result["target_business"] = {
        "website": website,
        "industry": industry,
        "location": location or "",
        "business_name": resolved_business_name,
        "summary": identity.get("summary", ""),
        "core_offer": identity.get("core_offer", ""),
    }

    return result
