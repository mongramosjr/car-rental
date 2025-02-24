from django.urls import path
from .views import (
    SelfieUploadView,
    IDCardUploadView,
    SelfieWithIDUploadView,
    VerificationStatusView,
    GetDecryptedImageView
)

urlpatterns = [
    path('api/verification/upload-selfie/', SelfieUploadView.as_view(), name='upload_selfie'),
    path('api/verification/upload-id/', IDCardUploadView.as_view(), name='upload_id'),
    path('api/verification/upload-selfie-with-id/', SelfieWithIDUploadView.as_view(), name='upload_selfie_with_id'),
    path('api/verification/status/', VerificationStatusView.as_view(), name='verification_status'),
    path('api/verification/get-image/<str:image_type>/', GetDecryptedImageView.as_view(), name='get_decrypted_image'),
]
