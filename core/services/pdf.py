from io import BytesIO
from datetime import datetime, timedelta
import random
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

W, H = A4
PAD  = 36

# ── Colours ───────────────────────────────────────────────────────────────────
DARK    = HexColor("#0f172a")
DARK2   = HexColor("#1e293b")
BLUE    = HexColor("#2563eb")
BLUELT  = HexColor("#eff6ff")
BLUEBD  = HexColor("#bfdbfe")
WHITE   = HexColor("#ffffff")
TEXT    = HexColor("#0f172a")
MUTED   = HexColor("#6b7280")
LIGHT   = HexColor("#94a3b8")
BORDER  = HexColor("#e2e8f0")
BG      = HexColor("#f8fafc")
PURPLE  = HexColor("#7c3aed")
TEAL    = HexColor("#0891b2")
GREEN   = HexColor("#059669")
AMBER   = HexColor("#d97706")

LANG_COLORS = {
    "TypeScript": "#2563eb", "JavaScript": "#d97706",
    "Python":     "#7c3aed", "Go":         "#0891b2",
    "Rust":       "#dc2626", "Java":       "#dc2626",
    "C++":        "#059669", "Shell":      "#059669",
    "HTML":       "#ea580c", "CSS":        "#2563eb",
    "Ruby":       "#dc2626", "Swift":      "#f59e0b",
    "Kotlin":     "#7c3aed", "PHP":        "#6366f1",
}

HEAT_COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

def lang_color(lang):
    return HexColor(LANG_COLORS.get(lang, "#6b7280"))

def heat_color(count):
    if count == 0:    return HexColor(HEAT_COLORS[0])
    elif count <= 3:  return HexColor(HEAT_COLORS[1])
    elif count <= 8:  return HexColor(HEAT_COLORS[2])
    elif count <= 15: return HexColor(HEAT_COLORS[3])
    else:             return HexColor(HEAT_COLORS[4])


# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_rect(c, x, y, w, h, fill=None, stroke=None, radius=4):
    """Draw a rounded rectangle. y is the BOTTOM-LEFT corner (ReportLab coords)."""
    p = c.beginPath()
    p.roundRect(x, y, w, h, radius)
    c.setLineWidth(0.5)
    if fill:   c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke)
    if fill and stroke: c.drawPath(p, fill=1, stroke=1)
    elif fill:          c.drawPath(p, fill=1, stroke=0)
    elif stroke:        c.drawPath(p, fill=0, stroke=1)


def section_title(c, title, y):
    """Draw a section label + hairline rule. Returns y for next content."""
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(LIGHT)
    c.drawString(PAD, y, title.upper())
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(PAD, y - 5, W - PAD, y - 5)
    return y - 18


def build_heatmap(seed=42):
    """
    Return a list of 364 dicts: {date, count}.
    Replace this with real GitHub contribution data from your API.
    Expected shape from your github service:
        data["contributions"]["heatmap"] = [{"date": "2024-05-07", "count": 3}, ...]
    """
    random.seed(seed)
    today = datetime.today()
    start = today - timedelta(weeks=52)
    days  = []
    for i in range(364):
        d = start + timedelta(days=i)
        r = random.random()
        if r < 0.45:   count = 0
        elif r < 0.70: count = random.randint(1, 3)
        elif r < 0.88: count = random.randint(4, 8)
        elif r < 0.96: count = random.randint(9, 15)
        else:          count = random.randint(16, 25)
        days.append({"date": d, "count": count})
    return days


# ── Main generator ────────────────────────────────────────────────────────────
def generate_pdf(data, summary, archetype):
    buf      = BytesIO()
    c        = canvas.Canvas(buf, pagesize=A4)
    profile  = data["profile"]
    contribs = data["contributions"]
    langs    = data["languages"]
    repos    = data["top_repos"]

    c.setTitle(f"{profile['name']} - GitFolio")

    # ── HEADER ────────────────────────────────────────────────────────────────
    HEADER_H = 110
    c.setFillColor(DARK)
    c.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)

    # Subtle gradient stripe at very top
    c.setFillColor(HexColor("#1e40af"))
    c.rect(0, H - 3, W, 3, fill=1, stroke=0)

    # Avatar
    cx_av, cy_av, r_av = PAD + 26, H - 55, 26
    c.setFillColor(BLUE)
    c.circle(cx_av, cy_av, r_av, fill=1, stroke=0)
    initials = "".join(w[0] for w in profile["name"].split()[:2]).upper()
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx_av, cy_av - 5, initials)

    # Name + handle
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 19)
    c.drawString(PAD + 62, H - 32, profile["name"])
    c.setFillColor(HexColor("#64748b"))
    c.setFont("Helvetica", 9)
    c.drawString(PAD + 62, H - 46, f"@{profile['username']}")

    # Location / company tags
    tag_x = PAD + 62
    for tag in filter(None, [profile.get("location"), profile.get("company")]):
        tw = c.stringWidth(tag, "Helvetica", 8) + 16
        draw_rect(c, tag_x, H - 70, tw, 14, fill=DARK2, radius=3)
        c.setFillColor(HexColor("#94a3b8"))
        c.setFont("Helvetica", 8)
        c.drawString(tag_x + 8, H - 64, tag)
        tag_x += tw + 5

    # Right-side meta
    joined = datetime.strptime(profile["created_at"], "%Y-%m-%dT%H:%M:%SZ").year
    meta   = [
        (f"Joined {joined}",                   HexColor("#64748b")),
        (f"{profile['followers']} followers",   HexColor("#64748b")),
        (f"{profile['public_repos']} repos",    HexColor("#64748b")),
        (f"github.com/{profile['username']}",   HexColor("#475569")),
    ]
    for i, (txt, col) in enumerate(meta):
        c.setFillColor(col)
        c.setFont("Helvetica", 8)
        c.drawRightString(W - PAD, H - 26 - i * 14, txt)

    y = H - HEADER_H - 12

    # ── DEVELOPER SUMMARY ─────────────────────────────────────────────────────
    y = section_title(c, "Developer Summary", y)

    BOX_H = 62
    draw_rect(c, PAD, y - BOX_H, W - PAD * 2, BOX_H, fill=BG, stroke=BORDER)
    c.setFillColor(BLUE)
    c.rect(PAD, y - BOX_H, 3, BOX_H, fill=1, stroke=0)

    style = ParagraphStyle("body", fontName="Helvetica", fontSize=8.5,
                           leading=13, textColor=TEXT)
    para  = Paragraph(summary, style)
    para.wrap(W - PAD * 2 - 22, BOX_H)
    para.drawOn(c, PAD + 10, y - BOX_H + 6)

    y -= BOX_H + 6

    # Archetype pill
    bw = c.stringWidth(archetype, "Helvetica-Bold", 8) + 24
    draw_rect(c, PAD, y - 16, bw, 16, fill=BLUELT, stroke=BLUEBD, radius=8)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(PAD + 9, y - 9, archetype)
    y -= 26

    # ── GITHUB AT A GLANCE ────────────────────────────────────────────────────
    y = section_title(c, "GitHub at a Glance", y)

    stats = [
        (f"{contribs['total']:,}",        "Total Contributions", True),
        (f"{contribs['commits']:,}",       "Commits",            False),
        (str(profile["public_repos"]),     "Repositories",       False),
        (f"{data['total_stars']:,}",       "Stars Earned",       False),
        (f"{profile['years_on_github']}y", "On GitHub",          False),
    ]
    N  = len(stats)
    cw = (W - PAD * 2) / N

    # outer border
    draw_rect(c, PAD, y - 44, W - PAD * 2, 44,
              fill=None, stroke=BORDER, radius=6)

    for i, (num, label, hi) in enumerate(stats):
        cx = PAD + i * cw
        fill = BLUELT if hi else WHITE
        r    = 6 if i == 0 else (6 if i == N - 1 else 0)
        draw_rect(c, cx, y - 44, cw, 44, fill=fill, radius=r)
        if i > 0:
            c.setStrokeColor(BORDER)
            c.setLineWidth(0.5)
            c.line(cx, y - 40, cx, y - 8)
        c.setFillColor(BLUE if hi else TEXT)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(cx + cw / 2, y - 24, num)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx + cw / 2, y - 36, label)

    y -= 54

    # ── CONTRIBUTIONS BREAKDOWN ───────────────────────────────────────────────
    y = section_title(c, "Contributions Breakdown", y)

    # Hero + mini tiles row
    HERO_W = 100
    draw_rect(c, PAD, y - 44, HERO_W, 44, fill=BLUELT, stroke=BLUEBD)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(PAD + 8, y - 26, f"{contribs['total']:,}")
    c.setFillColor(HexColor("#3b82f6"))
    c.setFont("Helvetica", 7.5)
    c.drawString(PAD + 8, y - 38, "Contributions this year")

    mini = [
        (contribs["this_month"],          "This month"),
        (contribs["this_week"],           "This week"),
        (f"{contribs['longest_streak']}d","Longest streak"),
        (f"{contribs['current_streak']}d","Current streak"),
    ]
    mini_w = (W - PAD * 2 - HERO_W - 8) / 4
    for i, (val, lbl) in enumerate(mini):
        mx = PAD + HERO_W + 8 + i * (mini_w + 3)
        draw_rect(c, mx, y - 44, mini_w - 3, 44, fill=BG, stroke=BORDER)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(mx + (mini_w - 3) / 2, y - 24, str(val))
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(mx + (mini_w - 3) / 2, y - 36, lbl)

    y -= 52

    # 4 metric pills
    cards  = [
        (contribs["commits"],       "Commits",       BLUE),
        (contribs["pull_requests"], "Pull Requests", PURPLE),
        (contribs["issues"],        "Issues",        TEAL),
        (contribs["reviews"],       "Code Reviews",  GREEN),
    ]
    pill_w = (W - PAD * 2 - 8 * 3) / 4
    for i, (val, lbl, col) in enumerate(cards):
        px = PAD + i * (pill_w + 8)
        draw_rect(c, px, y - 30, pill_w, 30, fill=BG, stroke=BORDER)
        c.setFillColor(col)
        c.circle(px + 11, y - 15, 4, fill=1, stroke=0)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(px + 20, y - 12, f"{val:,}")
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7)
        c.drawString(px + 20, y - 24, lbl)

    y -= 40

    # ── CONTRIBUTION HEATMAP ──────────────────────────────────────────────────
    y = section_title(c, "Contribution Activity - Past 12 Months", y)

    # Use real data if available: data["contributions"].get("heatmap", [])
    # Falls back to generated mock data
    raw_heatmap = data["contributions"].get("heatmap", [])
    if raw_heatmap:
        # flatten the 2D list of weeks → flat list of days
        flat = [day for week in raw_heatmap for day in week]
        heatmap_days = [
            {"date": datetime.strptime(d["date"], "%Y-%m-%d"), "count": d["count"]}
            for d in flat
        ]
    else:
        heatmap_days = build_heatmap()

    # Arrange into weeks (Mon-Sun columns)
    weeks   = []
    week    = []
    start_dow = heatmap_days[0]["date"].weekday()
    for _ in range(start_dow):
        week.append(None)
    for day in heatmap_days:
        week.append(day)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    CELL = 7
    GAP  = 2
    STEP = CELL + GAP
    grid_w = len(weeks) * STEP
    scale  = (W - PAD * 2) / grid_w
    CELL_S = CELL * scale
    STEP_S = STEP * scale

    # Month labels
    seen_months = set()
    c.setFont("Helvetica", 6.5)
    c.setFillColor(LIGHT)
    for wi, week in enumerate(weeks):
        for day in week:
            if day:
                m = day["date"].strftime("%b")
                if m not in seen_months:
                    seen_months.add(m)
                    c.drawString(PAD + wi * STEP_S, y - 2, m)
                break

    y -= 14

    # Draw cells
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = PAD + wi * STEP_S
            ry = y - di * (CELL_S + GAP * scale) - CELL_S
            if day:
                c.setFillColor(heat_color(day["count"]))
            else:
                c.setFillColor(HexColor("#f6f8fa"))
            p = c.beginPath()
            p.roundRect(x, ry, CELL_S, CELL_S, 1.5)
            c.drawPath(p, fill=1, stroke=0)

    heat_grid_h = 7 * (CELL_S + GAP * scale)
    y -= heat_grid_h + 4

    # Legend
    leg_labels = ["Less", "", "", "", "More"]
    leg_x      = W - PAD - (len(HEAT_COLORS) * 11 + 30)
    c.setFont("Helvetica", 7)
    c.setFillColor(LIGHT)
    c.drawString(leg_x, y - 2, "Less")
    for i, hc in enumerate(HEAT_COLORS):
        c.setFillColor(HexColor(hc))
        p = c.beginPath()
        p.roundRect(leg_x + 24 + i * 11, y - 8, 8, 8, 1.5)
        c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(LIGHT)
    c.drawString(leg_x + 24 + len(HEAT_COLORS) * 11 + 3, y - 2, "More")

    y -= 16

    # ── LANGUAGES & TECH STACK ────────────────────────────────────────────────
    y = section_title(c, "Languages & Tech Stack", y)

    bar_w = W - PAD * 2 - 80 - 36
    for lang in langs:
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(PAD, y - 2, lang["name"])
        # Track background
        draw_rect(c, PAD + 80, y - 7, bar_w, 5, fill=HexColor("#f1f5f9"), radius=2)
        # Fill bar
        fill_w = max(bar_w * lang["percentage"] / 100, 3)
        draw_rect(c, PAD + 80, y - 7, fill_w, 5, fill=lang_color(lang["name"]), radius=2)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7.5)
        c.drawString(PAD + 80 + bar_w + 6, y - 2, f"{lang['percentage']}%")
        y -= 15
    y -= 4

    # ── TOP REPOSITORIES ──────────────────────────────────────────────────────
    y = section_title(c, "Top Repositories", y)

    rw     = (W - PAD * 2 - 10) / 2
    REPO_H = 50
    for i, repo in enumerate(repos):
        rx = PAD + (i % 2) * (rw + 10)
        ry = y - (i // 2 + 1) * (REPO_H + 6)
        draw_rect(c, rx, ry, rw, REPO_H, fill=WHITE, stroke=BORDER)
        # Left accent bar
        c.setFillColor(lang_color(repo["language"]))
        c.rect(rx, ry, 3, REPO_H, fill=1, stroke=0)
        # Repo name
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(rx + 10, ry + REPO_H - 14, repo["name"])
        # Description
        desc = repo["description"]
        if len(desc) > 58:
            desc = desc[:58] + "..."
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawString(rx + 10, ry + REPO_H - 26, desc)
        # Language dot + meta
        c.setFillColor(lang_color(repo["language"]))
        c.circle(rx + 14, ry + 12, 3.5, fill=1, stroke=0)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7.5)
        c.drawString(rx + 22, ry + 9, f"{repo['language']}   * {repo['stars']}   f {repo['forks']}")

    y -= ((len(repos) + 1) // 2) * (REPO_H + 6) + 6

    # ── FOOTER ────────────────────────────────────────────────────────────────
    c.setFillColor(BG)
    c.rect(0, 0, W, 28, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(0, 28, W, 28)
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 7.5)
    c.drawString(PAD, 10, "Generated by GitFolio  -  free forever")
    month_year = datetime.utcnow().strftime("%B %Y")
    c.drawRightString(W - PAD, 10, f"{month_year}    github.com/{profile['username']}")

    c.save()
    return buf.getvalue()