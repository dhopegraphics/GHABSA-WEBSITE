from django.urls import path
from core.views import ContactUsCreateView, preview_recipients

urlpatterns = [
    path("contact-us/", ContactUsCreateView.as_view()),
    path("notifyuser/preview-recipients/", preview_recipients, name="preview_recipients"),
]
