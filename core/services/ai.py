import os

try:
    import anthropic
    from django.conf import settings
    HAS_KEY = bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-key-here")
except:
    HAS_KEY = False


def generate_summary(data):
    profile   = data["profile"]
    languages = data["languages"]
    contribs  = data["contributions"]
    top_repos = data["top_repos"]

    if not HAS_KEY:
        lang_str = ", ".join(l["name"] for l in languages[:3])
        return (
            f"{profile['name']} is a developer with {profile['years_on_github']} year(s) of GitHub activity, "
            f"primarily working in {lang_str}. "
            f"They have made {contribs['total']:,} total contributions with a longest streak of "
            f"{contribs['longest_streak']} days, showing consistent coding habits. "
            f"With {profile['public_repos']} public repositories and {profile['followers']} followers, "
            f"they demonstrate an active presence in the developer community."
        )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    lang_str = ", ".join(f"{l['name']} ({l['percentage']}%)" for l in languages)
    repo_str = ", ".join(f"{r['name']} ({r['language']}, ★{r['stars']})" for r in top_repos)

    prompt = f"""
You are writing a short professional developer bio for a PDF attached to a job application.

Developer data:
- Name: {profile['name']}
- Bio: {profile.get('bio') or 'Not provided'}
- Location: {profile.get('location') or 'Not provided'}
- Years on GitHub: {profile['years_on_github']}
- Public repos: {profile['public_repos']}
- Followers: {profile['followers']}
- Top languages: {lang_str}
- Total contributions: {contribs['total']}
- Commits: {contribs['commits']}
- PRs merged: {contribs['merged_prs']}
- Current streak: {contribs['current_streak']} days
- Longest streak: {contribs['longest_streak']} days
- Top repositories: {repo_str}

Write a 3 sentence professional summary in third person. Focus on experience level,
coding habits and consistency, and collaboration or open source involvement.
Keep it concise and recruiter friendly. No bullet points.
""".strip()

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_archetype(data):
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

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
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

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
