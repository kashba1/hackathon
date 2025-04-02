from django.urls import path, include  # Import include to include router URLs
from .views import ManualReconView, MarkManualView, SomeAPI
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path("auto_recon/", SomeAPI.as_view(), name="recon"),
    path(
        "auto_recon/override",
        MarkManualView.as_view(),
        name="user-override",
    ),
    path("manual_recon/", ManualReconView.as_view(), name="manual-recon"),
]
