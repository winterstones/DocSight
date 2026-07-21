from django.urls import path
from .views import SearchView, ChatView, TagsView, UploadView, DownloadView

urlpatterns = [
    path("",        SearchView.as_view(), name="search"),
    path("chat/",   ChatView.as_view(),   name="search-chat"),
    path("tags/",   TagsView.as_view(),   name="search-tags"),
    path("upload/", UploadView.as_view(), name="search-upload"),
    path("documents/<str:doc_id>/download/", DownloadView.as_view(), name="search-download"),
]
