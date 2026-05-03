from django.urls import path
from . import views

urlpatterns = [
    path("",                          views.index,       name="index"),
    path("examples/",                 views.examples,    name="examples"),
    path("preview/<str:username>/",   views.preview,     name="preview"),
    path("api/profile/<str:username>/", views.api_profile, name="api_profile"),
    path("api/pdf/<str:username>/",   views.api_pdf,     name="api_pdf"),
]
