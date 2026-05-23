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


def _calc_years_on_github(created_at_str: str) -> int:
    """
    Return the number of full calendar years since the account was created.
    e.g. created Jan 2022, now May 2026 → 4 years
         created Nov 2024, now May 2026 → 1 year
    Always at least 1 if any activity exists.
    """
    created = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
    now     = datetime.utcnow()
    years   = now.year - created.year
    # Subtract 1 if we haven't passed the anniversary month/day yet this year
    if (now.month, now.day) < (created.month, created.day):
        years -= 1
    return max(years, 1)


# ── 1. Basic profile ──────────────────────────────────────────────────────────
def fetch_profile(username: str) -> dict:
    r = requests.get(
        f"{REST_BASE}/users/{username}",
        headers=_headers(),
        timeout=10,
    )
    if r.status_code == 404:
        raise ValueError(f"GitHub user '{username}' not found.")
    r.raise_for_status()
    d = r.json()

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
        # Correctly computed: calendar years elapsed since account creation
        "years_on_github": _calc_years_on_github(d["created_at"]),
    }


# ── 2. Repositories + languages ───────────────────────────────────────────────
def fetch_repos(username: str) -> dict:
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
def fetch_contributions(username: str) -> dict:
    """
    Fetches contribution data using an explicit 12-month window (from → to)
    so the calendar always covers exactly the past 365 days regardless of
    where we are in the calendar year.  This prevents the streak from being
    cut off at a year boundary.
    """
    now   = datetime.utcnow()
    # GitHub requires ISO 8601 with timezone offset
    to_dt   = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    from_dt = (now.replace(year=now.year - 1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
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
        json={
            "query":     query,
            "variables": {"username": username, "from": from_dt, "to": to_dt},
        },
        headers=_headers(),
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()

    if "errors" in body:
        raise ValueError(body["errors"][0]["message"])

    user = body["data"]["user"]
    col  = user["contributionsCollection"]
    cal  = col["contributionCalendar"]

    # Flat sorted list of all days in the 12-month window
    all_days = sorted(
        [d for w in cal["weeks"] for d in w["contributionDays"]],
        key=lambda d: d["date"],
    )

    this_month = sum(
        d["contributionCount"] for d in all_days
        if d["date"][:7] == now.strftime("%Y-%m")
    )
    this_week = sum(
        d["contributionCount"]
        for d in (cal["weeks"][-1]["contributionDays"] if cal["weeks"] else [])
    )

    # Build heatmap (all 52 weeks)
    heatmap = []
    for week in cal["weeks"]:
        row = []
        for day in week["contributionDays"]:
            cnt   = day["contributionCount"]
            level = (
                0 if cnt == 0  else
                1 if cnt <= 2  else
                2 if cnt <= 5  else
                3 if cnt <= 9  else
                4
            )
            row.append({"date": day["date"], "count": cnt, "level": level})
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


def _calc_streak(days: list) -> dict:
    """
    Calculate current and longest contribution streaks.

    days: list of dicts with keys 'date' (str YYYY-MM-DD) and
          'contributionCount' (int), sorted ascending by date.

    Longest streak: the longest unbroken run of days with contributions.

    Current streak: consecutive days with contributions counting back from
    the most recent active day.  We allow today to be empty (it's still
    early in the day) and start counting from yesterday if today has 0.
    """
    sorted_days = sorted(days, key=lambda d: d["date"])

    # ── Longest ───────────────────────────────────────────────────────────────
    longest = temp = 0
    for day in sorted_days:
        if day["contributionCount"] > 0:
            temp   += 1
            longest = max(longest, temp)
        else:
            temp = 0

    # ── Current ───────────────────────────────────────────────────────────────
    # Walk backwards; skip the very last day if it has 0 contributions
    # (user hasn't committed yet today — don't break the streak for that)
    reversed_days = list(reversed(sorted_days))
    start_index   = 0
    if reversed_days and reversed_days[0]["contributionCount"] == 0:
        start_index = 1  # skip today's empty slot

    current = 0
    for day in reversed_days[start_index:]:
        if day["contributionCount"] > 0:
            current += 1
        else:
            break

    return {"current": current, "longest": longest}


# ── 4. Master fetch ───────────────────────────────────────────────────────────
def fetch_all(username: str) -> dict:
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
