import json
from anthropic import Anthropic
from app.config import settings


async def hermes_match_freelancers(
    project: dict,
    candidates: list[dict],
    n: int = 10,
) -> list[str]:
    """
    Use Claude to semantically rank freelancer candidates against a project brief.
    Returns ordered list of up to n freelancer user_ids, best match first.
    """
    if not candidates:
        return []

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    candidate_text = ""
    for i, c in enumerate(candidates):
        skills = ", ".join((c.get("skills") or [])[:15])
        areas = ", ".join(c.get("interest_areas") or [])
        candidate_text += f"""
[{i}] ID: {c['user_id']}
Headline: {c.get('headline', 'N/A')}
Skills: {skills}
Interest Areas: {areas}
Summary: {c.get('summary', 'N/A')}
---"""

    brief = (project.get("written_brief") or "N/A")[:500]
    project_text = f"""
Title: {project.get('title', 'N/A')}
Category: {project.get('category', 'N/A')}
Description: {project.get('description', 'N/A')}
Timeline: {project.get('timeline_value', 'N/A')} {project.get('timeline_unit', '')}
Brief: {brief}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="""You are Hermes, a freelance matching agent.
Rank the candidates by how well they match the project.
Consider: skill overlap, expertise relevance, experience level.
Return ONLY a JSON array of user_id strings, best match first.
Return at most the number requested. No explanation.""",
        messages=[
            {
                "role": "user",
                "content": f"""Project:\n{project_text}\n\nCandidates:\n{candidate_text}

Return the top {min(n, len(candidates))} user_ids as JSON array.""",
            }
        ],
    )

    ranked_ids = json.loads(response.content[0].text)
    return ranked_ids[:n]
