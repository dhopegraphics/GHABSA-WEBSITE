from django.urls import path
from .views import (
    SocietyHistoryListView,
    SocietyHistoryDetailView,
    SocietyHistoryByCategoryView,
    SocietyHistoryByYearView,
    HistoryCategoriesView,
    HistoryYearsView,
)

urlpatterns = [
    # List all history records
    path("", SocietyHistoryListView.as_view(), name="history-list"),
    
    # Get specific history record by ID
    path("<uuid:history_id>/", SocietyHistoryDetailView.as_view(), name="history-detail"),
    
    # Filter by category
    path("category/<str:category>/", SocietyHistoryByCategoryView.as_view(), name="history-by-category"),
    
    # Filter by year
    path("year/<str:year>/", SocietyHistoryByYearView.as_view(), name="history-by-year"),
    
    # Get available categories
    path("meta/categories/", HistoryCategoriesView.as_view(), name="history-categories"),
    
    # Get available years
    path("meta/years/", HistoryYearsView.as_view(), name="history-years"),
]
