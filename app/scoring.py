def compute_weighted_score(presence: int, engagement: int, automation: int) -> float:
    weights = {
        "presence": 0.40,
        "engagement": 0.35,
        "automation": 0.25,
    }

    score = (
        presence * weights["presence"] +
        engagement * weights["engagement"] +
        automation * weights["automation"]
    )
    return round(score, 2)


def assign_grade(score: float) -> str:
    if score >= 8.5:
        return "A"
    if score >= 7.0:
        return "B"
    if score >= 5.5:
        return "C"
    if score >= 4.0:
        return "D"
    return "E"


def enrich_competitor_scores(competitors: list) -> list:
    enriched = []

    for comp in competitors:
        presence = int(comp.get("presence", 0))
        engagement = int(comp.get("engagement", 0))
        automation = int(comp.get("automation", 0))

        weighted_score = compute_weighted_score(presence, engagement, automation)
        grade = assign_grade(weighted_score)

        enriched.append({
            **comp,
            "weighted_score": weighted_score,
            "grade": grade,
        })

    return sorted(enriched, key=lambda x: x["weighted_score"], reverse=True)


def compute_market_summary(competitors: list) -> dict:
    if not competitors:
        return {
            "average_score": 0,
            "top_score": 0,
            "average_grade": "N/A",
        }

    scores = [c["weighted_score"] for c in competitors]
    avg_score = round(sum(scores) / len(scores), 2)
    top_score = max(scores)

    return {
        "average_score": avg_score,
        "top_score": top_score,
        "average_grade": assign_grade(avg_score),
    }