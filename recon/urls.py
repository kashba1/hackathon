from django.urls import path, include  # Import include to include router URLs
from .views import (
    FileUploadView,
    ManualReconView,
    MarkManualView,
    RawMt940ViewSet,
    RawSapViewSet,
    SomeAPI,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"raw_sap", RawSapViewSet)
router.register(r"raw_mt940", RawMt940ViewSet)

urlpatterns = [
    path("", include(router.urls)),  
    path("upload/", FileUploadView.as_view(), name="upload-file"),
    path("auto_recon/", SomeAPI.as_view(), name="recon"),
    path(
        "auto_recon/override",
        MarkManualView.as_view(),
        name="user-override",
    ),
    path("manual_recon/", ManualReconView.as_view(), name="manual-recon"),
]
