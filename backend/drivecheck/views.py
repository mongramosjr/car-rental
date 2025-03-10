from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import UserVerification
from .serializers import (
    SelfieUploadSerializer,
    IDCardUploadSerializer,
    SelfieWithIDSerializer,
    VerificationStatusSerializer
)
from django.http import HttpResponse


class BaseVerificationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_verification(self, user):
        verification, _ = UserVerification.objects.get_or_create(user=user)
        return verification


class SelfieUploadView(BaseVerificationView):
    def post(self, request):
        verification = self.get_verification(request.user)

        if verification.status != 'pending':
            return Response(
                {"detail": "Selfie already uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SelfieUploadSerializer(verification, data=request.data)
        if serializer.is_valid():
            serializer.save()
            verification.status = 'selfie_uploaded'
            verification.save()
            return Response(
                {"message": "Selfie uploaded successfully"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IDCardUploadView(BaseVerificationView):
    def post(self, request):
        verification = self.get_verification(request.user)

        serializer = IDCardUploadSerializer(
            verification,
            data=request.data,
            context={'verification': verification}
        )
        if serializer.is_valid():
            serializer.save()
            verification.status = 'id_uploaded'
            verification.save()
            return Response(
                {"message": "ID card uploaded successfully"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SelfieWithIDUploadView(BaseVerificationView):
    def post(self, request):
        verification = self.get_verification(request.user)

        serializer = SelfieWithIDSerializer(
            verification,
            data=request.data,
            context={'verification': verification}
        )
        if serializer.is_valid():
            serializer.save()
            verification.status = 'selfie_with_id_uploaded'
            verification.save()
            request.user.is_verified = True
            request.user.save()
            return Response(
                {"message": "Verification completed successfully"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerificationStatusView(BaseVerificationView):
    def get(self, request):
        verification = self.get_verification(request.user)
        serializer = VerificationStatusSerializer(verification)
        return Response(serializer.data)


class GetDecryptedImageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, image_type):
        verification = UserVerification.objects.get(user=request.user)
        image_types = {
            'selfie': verification.selfie_image,
            'id_card': verification.id_card_image,
            'selfie_with_id': verification.selfie_with_id_image
        }

        if image_type not in image_types:
            return Response({"detail": "Invalid image type"}, status=status.HTTP_400_BAD_REQUEST)

        image_field = image_types[image_type]
        if not image_field:
            return Response({"detail": f"No {image_type} uploaded"}, status=status.HTTP_404_NOT_FOUND)

        decrypted_content = verification.decrypt_image(image_field)
        if decrypted_content:
            return HttpResponse(decrypted_content, content_type="image/jpeg")
        return Response({"detail": "Decryption failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
