import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from app.scrapper import get_website_text, normalize_url
from app.search_engine import discover_competitor_candidates

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_business_identity(website: str, industry: str, business_text: str) -> dict:
    prompt = f"""
You are identifying a business from its website.

Website: {website}
Industry: {industry}

Website text:
\"\"\"
{business_text[:3000]}
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
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.choices[0].message.content.strip())


def select_best_competitors(
    business_name: str,
    industry: str,
    business_text: str,
    candidates: list
) -> list:
    prompt = f"""
You are selecting the most likely real competitors for a business.

Business name: {business_name}
Industry: {industry}

Business website summary text:
\"\"\"
{business_text[:2500]}
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
- Prefer real competitors selling similar services/products
- Exclude irrelevant sites, directories, media, review sites, and social profiles
- No markdown
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    data = json.loads(response.choices[0].message.content.strip())
    return data.get("competitors", [])


def compare_business_to_competitors(
    website: str,
    industry: str,
    business_text: str,
    competitors: list
) -> dict:
    competitor_data = []

    for comp in competitors:
        comp_name = comp.get("name", "Unknown Competitor")
        comp_website = comp.get("website", "")
        comp_text = get_website_text(comp_website) if comp_website else "No website provided."

        competitor_data.append({
            "name": comp_name,
            "website": comp_website,
            "text": comp_text[:4000]
        })

    prompt = f"""
You are an AI business audit assistant.

Target business website: {website}
Industry: {industry}

Target business website text:
\"\"\"
{business_text[:4000]}
\"\"\"

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
  ]
}}

Scoring:
- presence = professionalism, clarity, visibility of services/products, quality of web presence
- engagement = calls to action, conversion prompts, trust signals, contact flow, user engagement
- automation = visible chatbot, booking flow, self-service, smart ordering, AI or automated workflows

Rules:
- Scores must be 1 to 10
- Ground the reasoning in visible site evidence
- Be conservative where evidence is weak
- Recommendations should be realistic for SMEs
- No markdown
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.choices[0].message.content.strip())


def analyze_business(website: str, industry: str) -> dict:
    website = normalize_url(website)
    business_text = get_website_text(website)

    identity = extract_business_identity(
        website=website,
        industry=industry,
        business_text=business_text
    )

    business_name = identity.get("business_name", "Unknown Business")

    candidates = discover_competitor_candidates(
        business_name=business_name,
        industry=industry,
        target_website=website,
        max_results=8
    )

    competitors = select_best_competitors(
        business_name=business_name,
        industry=industry,
        business_text=business_text,
        candidates=candidates
    )

    result = compare_business_to_competitors(
        website=website,
        industry=industry,
        business_text=business_text,
        competitors=competitors
    )

    result["target_business"] = {
        "website": website,
        "industry": industry,
        "business_name": business_name,
        "summary": identity.get("summary", ""),
        "core_offer": identity.get("core_offer", "")
    }

    result["candidate_competitors"] = candidates
    return result