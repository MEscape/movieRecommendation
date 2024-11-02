from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="User Registration",
        request_body=RegisterSerializer,
        responses={
            status.HTTP_201_CREATED: "User created successfully.",
            status.HTTP_400_BAD_REQUEST: "Validation errors."
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()

        logger.info('User registered successfully.')
        return Response(tokens, status=status.HTTP_201_CREATED)

class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="User Login",
        request_body=LoginSerializer,
        responses={
            status.HTTP_200_OK: "Login successful.",
            status.HTTP_404_NOT_FOUND: "User not found.",
            status.HTTP_400_BAD_REQUEST: "Validation errors.",
            status.HTTP_403_FORBIDDEN: "User inactive or deleted."
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info('User logged in successfully.')
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
