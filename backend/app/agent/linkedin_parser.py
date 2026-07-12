import json
from bs4 import BeautifulSoup
from anthropic import Anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.models import FreelancerProfile


def extract_text_from_linkedin_html(raw_html: str) -> str:
    """Pre-process HTML to reduce tokens before sending to Claude."""
    soup = BeautifulSoup(raw_html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    sections = {
        "name": soup.find("h1"),
        "headline": soup.find("div", {"class": lambda c: c and "text-body-medium" in c}),
        "about": soup.find("section", {"id": "about"}),
        "experience": soup.find("section", {"id": "experience"}),
        "education": soup.find("section", {"id": "education"}),
        "skills": soup.find("section", {"id": "skills"}),
        "location": soup.find("span", {"class": lambda c: c and "text-body-small" in c}),
    }

    extracted = {}
    for key, element in sections.items():
        if element:
            extracted[key] = element.get_text(separator=" ", strip=True)

    return str(extracted)


async def hermes_parse_linkedin(user_id: str, raw_html: str, db: AsyncSession):
    """Use Claude to parse LinkedIn HTML into structured profile data."""
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    pre_processed = extract_text_from_linkedin_html(raw_html)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system="""You are Hermes, a profile extraction agent.
Extract structured data from LinkedIn profile text.
Return ONLY valid JSON, no explanation.

JSON structure:
{
  "name": string,
  "headline": string,
  "location": string,
  "summary": string (2-3 sentence professional summary you write),
  "skills": [string],
  "experience": [
    {
      "title": string,
      "company": string,
      "duration": string,
      "description": string
    }
  ],
  "education": [
    {
      "degree": string,
      "institution": string,
      "year": string
    }
  ],
  "inferred_categories": [string]
}""",
        messages=[
            {"role": "user", "content": f"Parse this LinkedIn profile data:\n\n{pre_processed}"}
        ],
    )

    parsed = json.loads(response.content[0].text)

    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return

    profile.linkedin_parsed = parsed
    profile.headline = parsed.get("headline")
    profile.summary = parsed.get("summary")
    profile.skills = parsed.get("skills", [])
    profile.experience = parsed.get("experience", [])
    profile.education = parsed.get("education", [])
    profile.location = parsed.get("location")

    if not profile.interest_areas:
        profile.interest_areas = parsed.get("inferred_categories", [])

    await db.commit()
