import requests
from datetime import datetime
from django.conf import settings

REST_BASE   = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"


def _headers():
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


# ── 1. Basic profile ──────────────────────────────────────────────────────────
def fetch_profile(username):
    r = requests.get(
        f"{REST_BASE}/users/{username}",
        headers=_headers(),
        timeout=10,
    )
    if r.status_code == 404:
        raise ValueError(f"GitHub user '{username}' not found.")
    r.raise_for_status()
    d = r.json()

    created  = datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    years    = (datetime.utcnow() - created).days // 365

    return {
        "name":            d.get("name") or d["login"],
        "username":        d["login"],
        "avatar":          d["avatar_url"],
        "bio":             d.get("bio") or "",
        "location":        d.get("location") or "",
        "company":         d.get("company") or "",
        "blog":            d.get("blog") or "",
        "followers":       d["followers"],
        "following":       d["following"],
        "public_repos":    d["public_repos"],
        "created_at":      d["created_at"],
        "years_on_github": years,
    }


# ── 2. Repositories + languages ───────────────────────────────────────────────
def fetch_repos(username):
    r = requests.get(
        f"{REST_BASE}/users/{username}/repos?per_page=100&sort=pushed",
        headers=_headers(),
        timeout=10,
    )
    r.raise_for_status()

    lang_count = {}
    repos      = []

    for repo in r.json():
        if repo["fork"]:
            continue
        lang = repo.get("language") or "Other"
        lang_count[lang] = lang_count.get(lang, 0) + 1
        repos.append({
            "name":        repo["name"],
            "description": repo.get("description") or "",
            "language":    lang,
            "stars":       repo["stargazers_count"],
            "forks":       repo["forks_count"],
            "url":         repo["html_url"],
        })

    top_repos   = sorted(repos, key=lambda r: r["stars"], reverse=True)[:4]
    total_stars = sum(r["stars"] for r in repos)

    total_langs = sum(lang_count.values()) or 1
    languages   = [
        {"name": lang, "percentage": round(count / total_langs * 100)}
        for lang, count in sorted(lang_count.items(), key=lambda x: -x[1])[:5]
    ]

    return {
        "repos":       repos,
        "top_repos":   top_repos,
        "total_stars": total_stars,
        "languages":   languages,
    }


# ── 3. Contributions via GraphQL ──────────────────────────────────────────────
def fetch_contributions(username):
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
        pullRequests(states: MERGED) { totalCount }
      }
    }
    """
    r = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": {"username": username}},
        headers=_headers(),
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()

    if "errors" in body:
        raise ValueError(body["errors"][0]["message"])

    user     = body["data"]["user"]
    col      = user["contributionsCollection"]
    cal      = col["contributionCalendar"]
    all_days = [d for w in cal["weeks"] for d in w["contributionDays"]]

    now        = datetime.utcnow()
    this_month = sum(
        d["contributionCount"] for d in all_days
        if d["date"][:7] == now.strftime("%Y-%m")
    )
    this_week = sum(
        d["contributionCount"]
        for d in (cal["weeks"][-1]["contributionDays"] if cal["weeks"] else [])
    )

    heatmap = []
    for week in cal["weeks"][-26:]:
        row = []
        for day in week["contributionDays"]:
            c = day["contributionCount"]
            level = 0 if c == 0 else 1 if c <= 2 else 2 if c <= 5 else 3 if c <= 9 else 4
            row.append({"date": day["date"], "count": c, "level": level})
        heatmap.append(row)

    streak = _calc_streak(all_days)

    return {
        "total":          cal["totalContributions"],
        "commits":        col["totalCommitContributions"],
        "pull_requests":  col["totalPullRequestContributions"],
        "merged_prs":     user["pullRequests"]["totalCount"],
        "issues":         col["totalIssueContributions"],
        "reviews":        col["totalPullRequestReviewContributions"],
        "this_month":     this_month,
        "this_week":      this_week,
        "current_streak": streak["current"],
        "longest_streak": streak["longest"],
        "heatmap":        heatmap,
    }


def _calc_streak(days):
    sorted_days = sorted(days, key=lambda d: d["date"], reverse=True)
    current = longest = temp = 0
    for i, d in enumerate(sorted_days):
        if d["contributionCount"] > 0:
            temp += 1
            if i == 0 or current == temp - 1:
                current = temp
            longest = max(longest, temp)
        else:
            temp = 0
    return {"current": current, "longest": longest}


# ── 4. Master function — fetch everything ─────────────────────────────────────
def fetch_all(username):
    profile   = fetch_profile(username)
    repo_data = fetch_repos(username)
    contribs  = fetch_contributions(username)

    return {
        "profile":       profile,
        "repos":         repo_data["repos"],
        "top_repos":     repo_data["top_repos"],
        "total_stars":   repo_data["total_stars"],
        "languages":     repo_data["languages"],
        "contributions": contribs,
    }
