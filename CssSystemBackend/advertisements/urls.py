from django.urls import path
from advertisements.views import GetAdsListView

urlpatterns = [
    path("", GetAdsListView.as_view(), name="ads"),
]
