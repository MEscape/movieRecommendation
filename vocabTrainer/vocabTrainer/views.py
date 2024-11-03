from django.http import HttpResponse
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
import os
import mimetypes

class SecureImageView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, image_path):
        token_param = request.GET.get("token") or request.headers.get("Authorization")
        if token_param and token_param.startswith("Bearer "):
            token_param = token_param.split(" ")[1]

        if not token_param:
            return Response(
                {
                    "detail": "Authentication credentials were not provided.",
                    "status_code": 401,
                    "default_code": "authentication_failed"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            AccessToken(token_param)
        except Exception as e:
            raise AuthenticationFailed("Invalid or expired token")

        full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

        if not os.path.exists(full_image_path):
            return Response(
                {
                    "detail": "Image does not exist",
                    "status_code": 404,
                    "default_code": "image_not_found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        mime_type, _ = mimetypes.guess_type(full_image_path)
        if mime_type not in ["image/jpeg", "image/png"]:
            return Response(
                {
                    "detail": "Unsupported image format",
                    "status_code": 415,
                    "default_code": "unsupported_media_type"
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        with open(full_image_path, 'rb') as image_file:
            return HttpResponse(image_file.read(), content_type=mime_type)
