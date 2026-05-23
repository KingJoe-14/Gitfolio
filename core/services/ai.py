from datetime import datetime
import os
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY", "")
HAS_KEY = bool(API_KEY and API_KEY != "your-openai-key-here")
client  = OpenAI(api_key=API_KEY) if HAS_KEY else None


def _years_label(profile: dict) -> str:
    created = datetime.strptime(profile["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    now     = datetime.utcnow()
    years   = now.year - created.year
    if (now.month, now.day) < (created.month, created.day):
        years -= 1
    years = max(years, 1)
    return f"{years} year{'s' if years != 1 else ''}"


def generate_summary(data: dict) -> str:
    profile   = data["profile"]
    languages = data["languages"]
    contribs  = data["contributions"]
    top_repos = data["top_repos"]
    years_str = _years_label(profile)

    if not HAS_KEY:
        lang_str = ", ".join(l["name"] for l in languages[:3])
        return (
            f"{profile['name']} is a developer with {years_str} of GitHub activity, "
            f"primarily working in {lang_str}. "
            f"They have made {contribs['total']:,} total contributions with a longest streak of "
            f"{contribs['longest_streak']} days, showing consistent coding habits. "
            f"With {profile['public_repos']} public repositories and {profile['followers']} followers, "
            f"they demonstrate an active presence in the developer community."
        )

    lang_str = ", ".join(f"{l['name']} ({l['percentage']}%)" for l in languages)
    repo_str = ", ".join(
        f"{r['name']} ({r['language']}, ⭐{r['stars']})" for r in top_repos
    )

    prompt = f"""
You are writing a short professional developer bio for a PDF attached to a job application.

Developer data:
- Name: {profile['name']}
- Bio: {profile.get('bio') or 'Not provided'}
- Location: {profile.get('location') or 'Not provided'}
- Years on GitHub: {years_str}
- Public repos: {profile['public_repos']}
- Followers: {profile['followers']}
- Top languages: {lang_str}
- Total contributions (past 12 months): {contribs['total']}
- Commits: {contribs['commits']}
- PRs merged: {contribs['merged_prs']}
- Current streak: {contribs['current_streak']} days
- Longest streak: {contribs['longest_streak']} days
- Top repositories: {repo_str}

Write a 3 sentence professional summary in third person. Focus on experience level,
coding habits and consistency, and collaboration or open source involvement.
Keep it concise and recruiter-friendly. No bullet points.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def generate_archetype(data: dict) -> str:
    languages = data["languages"]
    contribs  = data["contributions"]

    if not HAS_KEY:
        lang = languages[0]["name"] if languages else "Code"
        if contribs["total"] > 1000:
            return f"{lang} Developer · Active Contributor · Consistent Builder"
        elif contribs["merged_prs"] > 20:
            return f"{lang} Developer · Open Source Contributor"
        else:
            return f"{lang} Developer · Consistent Builder"

    prompt = f"""
Based on this developer's data generate 2 to 3 short archetype tags, each 2 to 3 words max.

Data:
- Top languages: {', '.join(l['name'] for l in languages)}
- Total contributions: {contribs['total']}
- Commits: {contribs['commits']}
- PRs merged: {contribs['merged_prs']}
- Current streak: {contribs['current_streak']} days

Examples: Backend Specialist, Active Contributor, Consistent Builder,
Frontend Expert, Open Source Advocate, Polyglot Developer

Return ONLY the tags separated by · with no other text.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()