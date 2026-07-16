from django.urls import path
from news.views import GetAllNewsViews

urlpatterns = [
    path("", GetAllNewsViews.as_view(), name="all-news"),
]
