from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

W, H  = A4
PAD   = 36

# ── Colours ───────────────────────────────────────────────────────────────────
DARK   = HexColor("#0f1117")
BLUE   = HexColor("#2563eb")
BLUELT = HexColor("#eff6ff")
BLUEBD = HexColor("#bfdbfe")
WHITE  = HexColor("#ffffff")
TEXT   = HexColor("#1a1a1a")
MUTED  = HexColor("#6b7280")
LIGHT  = HexColor("#9ca3af")
BORDER = HexColor("#e5e7eb")
BG     = HexColor("#f9fafb")
PURPLE = HexColor("#7c3aed")
TEAL   = HexColor("#0891b2")
GREEN  = HexColor("#059669")

LANG_COLORS = {
    "TypeScript": "#2563eb", "JavaScript": "#d97706",
    "Python":     "#7c3aed", "Go":         "#0891b2",
    "Rust":       "#dc2626", "Java":       "#dc2626",
    "C++":        "#059669", "Shell":      "#059669",
    "HTML":       "#ea580c", "CSS":        "#2563eb",
    "Ruby":       "#dc2626", "Swift":      "#f59e0b",
    "Kotlin":     "#7c3aed", "PHP":        "#7c3aed",
}

def lang_color(lang):
    return HexColor(LANG_COLORS.get(lang, "#6b7280"))


# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_section_title(c, title, y):
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(LIGHT)
    c.drawString(PAD, y, title.upper())
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(PAD, y - 4, W - PAD, y - 4)
    return y - 18


def draw_rect(c, x, y, w, h, fill=None, stroke=None, radius=4):
    p = c.beginPath()
    p.roundRect(x, y, w, h, radius)
    c.setLineWidth(0.5)
    if fill:   c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke)
    if fill and stroke: c.drawPath(p, fill=1, stroke=1)
    elif fill:          c.drawPath(p, fill=1, stroke=0)
    elif stroke:        c.drawPath(p, fill=0, stroke=1)


# ── Main PDF generator ────────────────────────────────────────────────────────
def generate_pdf(data, summary, archetype):
    buf      = BytesIO()
    c        = canvas.Canvas(buf, pagesize=A4)
    profile  = data["profile"]
    contribs = data["contributions"]
    langs    = data["languages"]
    repos    = data["top_repos"]

    c.setTitle(f"{profile['name']} — GitFolio")

    # ── HEADER ────────────────────────────────────────────────────────────────
    c.setFillColor(DARK)
    c.rect(0, H - 108, W, 108, fill=1, stroke=0)

    # Avatar circle with initials
    initials = "".join(w[0] for w in profile["name"].split()[:2]).upper()
    c.setFillColor(BLUE)
    c.circle(PAD + 26, H - 54, 26, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(PAD + 26, H - 59, initials)

    # Name
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(PAD + 64, H - 34, profile["name"])

    # Username
    c.setFillColor(HexColor("#6b7280"))
    c.setFont("Helvetica", 9)
    c.drawString(PAD + 64, H - 48, f"@{profile['username']}")

    # Location and company tags
    tag_x = PAD + 64
    for tag in filter(None, [profile.get("location"), profile.get("company")]):
        tw = c.stringWidth(tag, "Helvetica", 8) + 14
        draw_rect(c, tag_x, H - 70, tw, 15, fill=HexColor("#1e2330"))
        c.setFillColor(HexColor("#9ca3af"))
        c.setFont("Helvetica", 8)
        c.drawString(tag_x + 7, H - 64, tag)
        tag_x += tw + 6

    # Right side meta info
    joined = datetime.strptime(profile["created_at"], "%Y-%m-%dT%H:%M:%SZ").year
    meta   = [
        f"Joined {joined}",
        f"{profile['followers']} followers",
        f"{profile['public_repos']} repos",
        f"github.com/{profile['username']}",
    ]
    c.setFont("Helvetica", 8)
    for i, txt in enumerate(meta):
        c.setFillColor(HexColor("#6b7280") if i < 3 else HexColor("#4b5563"))
        c.drawRightString(W - PAD, H - 28 - i * 14, txt)

    y = H - 122

    # ── DEVELOPER SUMMARY ────────────────────────────────────────────────────
    y = draw_section_title(c, "Developer Summary", y)

    draw_rect(c, PAD, y - 65, W - PAD * 2, 65, fill=BG, stroke=BORDER)
    c.setFillColor(BLUE)
    c.rect(PAD, y - 65, 3, 65, fill=1, stroke=0)

    style = ParagraphStyle("s", fontName="Helvetica", fontSize=8.5,
                           leading=13, textColor=TEXT)
    para  = Paragraph(summary, style)
    para.wrap(W - PAD * 2 - 22, 65)
    para.drawOn(c, PAD + 10, y - 58)

    y -= 73

    # Archetype badge
    bw = c.stringWidth(archetype, "Helvetica-Bold", 8) + 26
    draw_rect(c, PAD, y - 17, bw, 17, fill=BLUELT, stroke=BLUEBD)
    c.setFillColor(BLUE)
    c.rect(PAD, y - 17, 3, 17, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(BLUE)
    c.drawString(PAD + 10, y - 10, archetype)
    y -= 27

    # ── GITHUB AT A GLANCE ───────────────────────────────────────────────────
    y = draw_section_title(c, "GitHub at a Glance", y)

    stats   = [
        (f"{contribs['total']:,}",         "Total Contributions", True),
        (f"{contribs['commits']:,}",        "Commits",            False),
        (str(profile["public_repos"]),      "Repositories",       False),
        (f"{data['total_stars']:,}",        "Stars Earned",       False),
        (f"{profile['years_on_github']}y",  "On GitHub",          False),
    ]
    cw = (W - PAD * 2 - 8 * 4) / 5
    for i, (num, label, hi) in enumerate(stats):
        cx = PAD + i * (cw + 8)
        draw_rect(c, cx, y - 42, cw, 42,
                  fill=BLUELT if hi else BG,
                  stroke=BLUEBD if hi else BORDER)
        c.setFillColor(BLUE if hi else TEXT)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(cx + cw / 2, y - 24, num)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx + cw / 2, y - 36, label)
    y -= 52

    # ── CONTRIBUTIONS BREAKDOWN ──────────────────────────────────────────────
    y = draw_section_title(c, "Contributions Breakdown", y)

    # Summary row
    draw_rect(c, PAD, y - 42, W - PAD * 2, 42, fill=BG, stroke=BORDER)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(PAD + 10, y - 26, f"{contribs['total']:,}")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(PAD + 10, y - 37, "Contributions this year")

    c.setStrokeColor(BORDER)
    c.line(PAD + 112, y - 38, PAD + 112, y - 8)

    for i, (val, lbl) in enumerate([(contribs["this_month"], "This month"),
                                     (contribs["this_week"],  "This week")]):
        cx = PAD + 122 + i * 72
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(cx, y - 24, str(val))
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7)
        c.drawString(cx, y - 35, lbl)

    c.setStrokeColor(BORDER)
    c.line(PAD + 266, y - 38, PAD + 266, y - 8)

    for i, (val, lbl) in enumerate([(f"{contribs['longest_streak']}d", "Longest streak"),
                                     (f"{contribs['current_streak']}d", "Current streak")]):
        cx = PAD + 276 + i * 84
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(cx, y - 24, val)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7)
        c.drawString(cx, y - 35, lbl)

    y -= 50

    # Four breakdown cards
    bw2   = (W - PAD * 2 - 8 * 3) / 4
    cards = [
        (contribs["commits"],       "Commits",       BLUE),
        (contribs["pull_requests"], "Pull Requests",  PURPLE),
        (contribs["issues"],        "Issues",         TEAL),
        (contribs["reviews"],       "Code Reviews",   GREEN),
    ]
    for i, (val, lbl, col) in enumerate(cards):
        cx = PAD + i * (bw2 + 8)
        draw_rect(c, cx, y - 34, bw2, 34, fill=BG, stroke=BORDER)
        c.setFillColor(col)
        c.circle(cx + 11, y - 17, 4, fill=1, stroke=0)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(cx + 21, y - 14, f"{val:,}")
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7)
        c.drawString(cx + 21, y - 26, lbl)
    y -= 44

    # ── LANGUAGES ────────────────────────────────────────────────────────────
    y = draw_section_title(c, "Languages & Tech Stack", y)

    bar_w = W - PAD * 2 - 90 - 30
    for lang in langs:
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(PAD, y - 2, lang["name"])
        draw_rect(c, PAD + 92, y - 7, bar_w, 5, fill=HexColor("#f0f0f0"))
        fill_w = max(bar_w * lang["percentage"] / 100, 3)
        draw_rect(c, PAD + 92, y - 7, fill_w, 5, fill=lang_color(lang["name"]))
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7.5)
        c.drawString(PAD + 92 + bar_w + 6, y - 2, f"{lang['percentage']}%")
        y -= 15
    y -= 4

    # ── TOP REPOSITORIES ─────────────────────────────────────────────────────
    y = draw_section_title(c, "Top Repositories", y)

    rw = (W - PAD * 2 - 10) / 2
    for i, repo in enumerate(repos):
        rx = PAD + (i % 2) * (rw + 10)
        ry = y - (i // 2 + 1) * 52
        draw_rect(c, rx, ry, rw, 48, fill=WHITE, stroke=BORDER)
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(rx + 8, ry + 34, repo["name"])
        desc = repo["description"][:60] + "…" if len(repo["description"]) > 60 else repo["description"]
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawString(rx + 8, ry + 22, desc)
        c.setFillColor(lang_color(repo["language"]))
        c.circle(rx + 12, ry + 10, 3.5, fill=1, stroke=0)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7.5)
        c.drawString(rx + 20, ry + 7, f"{repo['language']}   ★ {repo['stars']}   ⑂ {repo['forks']}")

    y -= (len(repos) + 1) // 2 * 52 + 6

    # ── FOOTER ───────────────────────────────────────────────────────────────
    c.setFillColor(BG)
    c.rect(0, 0, W, 28, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(0, 28, W, 28)
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 7.5)
    c.drawString(PAD, 10, "Generated by GitFolio · free forever")
    month_year = datetime.utcnow().strftime("%B %Y")
    c.drawRightString(W - PAD, 10, f"{month_year}  ·  github.com/{profile['username']}")

    c.save()
    return buf.getvalue()
