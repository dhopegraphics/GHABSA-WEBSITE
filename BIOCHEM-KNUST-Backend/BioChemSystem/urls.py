"""

URL configuration for BioChemSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Import the seller admin site
from el_mercado.seller_admin import seller_admin_site


urlpatterns = [
    path("core/", include("core.urls")),
    path("accounts/", include("accounts.urls"), name="accounts"),
    path("news/", include("news.urls"), name="news"),
    path("timetable_system/", include("timetable_system.urls")),
    path("academics/", include("academics.urls"), name="academics"),
    path("timeline/", include("timeline.urls"), name="timeline"),
    path("executives/", include("executives.urls"), name="execs"),
    path("history/", include("history.urls"), name="history"),  # Society History System
    path("executive-dashboard-cb/", admin.site.urls, name="executive-dashboard-cb"),
    path("seller-dashboard/", seller_admin_site.urls, name="seller-dashboard"),  # El Mercado Seller Dashboard
    path("events/", include("events.urls"), name="events"),
    path("ads/", include("advertisements.urls"), name="ads"),
    path("products/", include("products.urls")),
    path("helpdesk/", include("helpdesk.urls"), name="helpdesk"),
    path("planner/", include("planner.urls"), name="planner"),
    path("faculty/", include("faculty.urls"), name="faculty"),
    path("projects/", include("projects.urls"), name="projects"),
    path("codequest/", include("codequest.urls"), name="codequest"),  # Code Quest Management System
    path("voting/", include("voting.urls"), name="voting"),  # Advanced Voting & Elections System
    path("payments/", include("payments.urls"), name="payments"),  # Universal Payment & Transaction System
    path("notifications/", include("notifications.urls"), name="notifications"),  # Push Notification System
    path("admissions/", include("admissions.urls"), name="admissions"),  # KNUST Admission Eligibility & Guidance System
    path("mentorship/", include("mentorship.urls"), name="mentorship"),  # Mentorship System
    path("donations/", include("donations.urls"), name="donations"),  # Public Donation System
    path("calendar/", include("calendar_sync.urls"), name="calendar"),  # Phone Calendar Synchronization System
    path("marketplace/", include("el_mercado.urls"), name="el_mercado"),  # El Mercado Multi-Vendor Marketplace
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "api-docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# Serve static and media files in development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
