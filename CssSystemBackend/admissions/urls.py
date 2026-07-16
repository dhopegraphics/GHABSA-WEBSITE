from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdmissionCriteriaViewSet, SubjectGradeMappingViewSet,
    AdmissionGuidelineViewSet, EligibilityCheckViewSet,
    FAQViewSet, ImportantDateViewSet, WhatsAppHelpdeskViewSet,
    AccommodationViewSet
)
from .scraper_views import (
    scraper_dashboard, run_scraper, download_excel, 
    clean_excel_duplicates, sync_excel_with_db, upload_excel, get_year_stats
)

app_name = 'admissions'

router = DefaultRouter()
router.register('criteria', AdmissionCriteriaViewSet, basename='admission-criteria')
router.register('grade-mappings', SubjectGradeMappingViewSet, basename='grade-mapping')
router.register('guidelines', AdmissionGuidelineViewSet, basename='guideline')
router.register('eligibility-check', EligibilityCheckViewSet, basename='eligibility-check')
router.register('faqs', FAQViewSet, basename='faq')
router.register('important-dates', ImportantDateViewSet, basename='important-date')
router.register('whatsapp-helpdesk', WhatsAppHelpdeskViewSet, basename='whatsapp-helpdesk')
router.register('accommodation', AccommodationViewSet, basename='accommodation')

urlpatterns = [
    path('', include(router.urls)),
    # Scraper URLs
    path('scraper/dashboard/', scraper_dashboard, name='scraper_dashboard'),
    path('scraper/run/', run_scraper, name='run_scraper'),
    path('scraper/download/', download_excel, name='download_excel'),
    path('scraper/clean-duplicates/', clean_excel_duplicates, name='clean_excel_duplicates'),
    path('scraper/sync-excel/', sync_excel_with_db, name='sync_excel_with_db'),
    path('scraper/upload/', upload_excel, name='upload_excel'),
    path('scraper/year-stats/', get_year_stats, name='get_year_stats'),
]
