from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/",      include("apps.authentication.api.urls")),
    path("api/search/",    include("apps.search.api.urls")),
    path("api/documents/", include("apps.documents.api.urls")),
]
