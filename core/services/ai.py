import anthropic
from django.conf import settings


def _client():
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


# ── 1. Generate the developer summary paragraph ───────────────────────────────
def generate_summary(data):
    profile   = data["profile"]
    languages = data["languages"]
    contribs  = data["contributions"]
    top_repos = data["top_repos"]

    lang_str = ", ".join(f"{l['name']} ({l['percentage']}%)" for l in languages)
    repo_str = ", ".join(f"{r['name']} ({r['language']}, ★{r['stars']})" for r in top_repos)

    prompt = f"""
You are writing a short professional developer bio for a PDF that will be attached to a job application.

Here is the developer's data:
- Name: {profile['name']}
- Bio: {profile.get('bio') or 'Not provided'}
- Location: {profile.get('location') or 'Not provided'}
- Years on GitHub: {profile['years_on_github']}
- Public repos: {profile['public_repos']}
- Followers: {profile['followers']}
- Top languages: {lang_str}
- Total contributions this year: {contribs['total']}
- Total commits: {contribs['commits']}
- Pull requests merged: {contribs['merged_prs']}
- Issues raised: {contribs['issues']}
- Current streak: {contribs['current_streak']} days
- Longest streak: {contribs['longest_streak']} days
- Top repositories: {repo_str}

Write a 3 sentence professional summary in third person. Focus on:
1. Their experience level and main specialisation
2. Their coding habits and consistency
3. Their collaboration or open source involvement

Keep it concise and recruiter friendly. No bullet points. Do not mention GitHub explicitly.
""".strip()

    message = _client().messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


# ── 2. Generate archetype tags ────────────────────────────────────────────────
def generate_archetype(data):
    languages = data["languages"]
    contribs  = data["contributions"]
    top_repos = data["top_repos"]

    prompt = f"""
Based on this developer's data generate 2 to 3 short archetype tags, each 2 to 3 words max.

Data:
- Top languages: {', '.join(l['name'] for l in languages)}
- Total contributions: {contribs['total']}
- Commits: {contribs['commits']}
- PRs merged: {contribs['merged_prs']}
- Current streak: {contribs['current_streak']} days
- Top repos: {', '.join(r['name'] for r in top_repos)}

Examples of good tags: Backend Specialist, Active Contributor, Consistent Builder,
Frontend Expert, Open Source Advocate, Polyglot Developer, Full Stack Engineer

Return ONLY the tags separated by · with no other text.
""".strip()

    message = _client().messages.create(
        model="claude-opus-4-5",
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
