import json
from anthropic import Anthropic
from openai import OpenAI
from app.config import settings


async def hermes_match_freelancers(
    project: dict,
    candidates: list[dict],
    n: int = 10,
) -> list[str]:
    """
    Use Claude to semantically rank freelancer candidates against a project brief.
    Falls back to DeepSeek if Anthropic fails.
    Returns ordered list of up to n freelancer user_ids, best match first.
    """
    if not candidates:
        return []

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

    system_prompt = """You are Hermes, a freelance matching agent.
Rank the candidates by how well they match the project.
Consider: skill overlap, expertise relevance, experience level.
Return ONLY a JSON array of user_id strings, best match first.
Return at most the number requested. No explanation."""

    user_msg = f"""Project:\n{project_text}\n\nCandidates:\n{candidate_text}

Return the top {min(n, len(candidates))} user_ids as JSON array."""

    # Try Anthropic first
    try:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        ranked_ids = json.loads(response.content[0].text)
        return ranked_ids[:n]
    except Exception as e:
        print(f"[Hermes] Anthropic failed, trying DeepSeek fallback: {e}")

    # Fallback to DeepSeek
    if settings.DEEPSEEK_API_KEY:
        try:
            client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=1000,
            )
            ranked_ids = json.loads(response.choices[0].message.content)
            return ranked_ids[:n]
        except Exception as e:
            print(f"[Hermes] DeepSeek fallback also failed: {e}")

    # Last resort: return candidates in original order
    return [c["user_id"] for c in candidates[:n]]
