from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET

from .services.github import fetch_all
from .services.ai import generate_summary, generate_archetype
from .services.pdf import generate_pdf


# ── Pages ─────────────────────────────────────────────────────────────────────
def index(request):
    return render(request, "core/index.html")


def examples(request):
    devs = [
        {
            "name": "Kingsley Thompson", "username": "KingJoe-14",
            "initials": "KT", "color": "#1d4ed8",
            "contributions": "2,341", "repos": 47, "years": 5,
            "tags": ["TypeScript", "Python", "Go"],
        },
        {
            "name": "Paapa Kwesi Bentil", "username": "PBentil",
            "initials": "PKB", "color": "#059669",
            "contributions": "1,890", "repos": 32, "years": 3,
            "tags": ["React", "Vue", "CSS"],
        },
        {
            "name": "Kwame Osei", "username": "kwameosei",
            "initials": "KO", "color": "#7c3aed",
            "contributions": "4,102", "repos": 91, "years": 7,
            "tags": ["Rust", "C++", "Linux"],
        },
        {
            "name": "Sara Asante", "username": "saraasante",
            "initials": "SA", "color": "#d97706",
            "contributions": "987", "repos": 18, "years": 2,
            "tags": ["Swift", "Kotlin"],
        },
        {
            "name": "Eli Boateng", "username": "eliboateng",
            "initials": "EB", "color": "#dc2626",
            "contributions": "3,210", "repos": 60, "years": 6,
            "tags": ["Django", "PostgreSQL", "AWS"],
        },
        {
            "name": "Nana Mensah", "username": "nanamensah",
            "initials": "NM", "color": "#0891b2",
            "contributions": "1,540", "repos": 28, "years": 4,
            "tags": ["Node.js", "GraphQL", "Docker"],
        },
    ]
    return render(request, "core/examples.html", {"examples": devs})


def preview(request, username):
    return render(request, "core/preview.html", {"username": username})


# ── API endpoints ─────────────────────────────────────────────────────────────
@require_GET
def api_profile(request, username):
    try:
        data      = fetch_all(username)
        summary   = generate_summary(data)
        archetype = generate_archetype(data)
        return JsonResponse({
            "success":   True,
            "data":      data,
            "summary":   summary,
            "archetype": archetype,
        })
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": "Something went wrong. Please try again."}, status=500)


@require_GET
def api_pdf(request, username):
    try:
        data      = fetch_all(username)
        summary   = generate_summary(data)
        archetype = generate_archetype(data)
        pdf_bytes = generate_pdf(data, summary, archetype)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{username}-gitfolio.pdf"'
        return response
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": "Something went wrong. Please try again."}, status=500)
