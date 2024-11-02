from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from .exceptions import EmailAlreadyExistsException, UsernameAlreadyExistsException, UserNotFoundException, InactiveUserException
from .jwt import CustomTokenObtainPairSerializer

User = get_user_model()

class TokenMixin:
    @staticmethod
    def get_tokens_for_user(user):
        """
        Generate access and refresh tokens for the given user.

        Args:
            user (User): The user instance for which to generate tokens.

        Returns:
            dict: A dictionary containing the access and refresh tokens.
        """
        serializer = CustomTokenObtainPairSerializer()
        refresh = serializer.get_token(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_verify = serializers.CharField(write_only=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_verify', 'role')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'password_verify': {'write_only': True, 'style': {'input_type': 'password'}},
        }

    def validate(self, data):
        """
        Validate the registration data.

        Args:
            data (dict): The data to validate.

        Returns:
            dict: The validated data.

        Raises:
            serializers.ValidationError: If passwords do not match, email or username already exists.
        """
        request = self.context.get('request')

        if data.get('password') != data.get('password_verify'):
            raise serializers.ValidationError({"password": "Passwords must match."})

        if request and not request.user.is_staff:
            data.pop('role', None)

        if User.objects.filter(email=data.get('email')).exists():
            raise EmailAlreadyExistsException()
        if User.objects.filter(username=data.get('username')).exists():
            raise UsernameAlreadyExistsException()

        return data

    def create(self, validated_data):
        """
        Create a new user with the validated data.

        Args:
            validated_data (dict): The validated data for the new user.

        Returns:
            dict: The tokens for the newly created user.
        """
        validated_data.pop('password_verify', None)
        user = User.objects.create_user(**validated_data)
        tokens = TokenMixin.get_tokens_for_user(user)
        return tokens


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        """
        Validate login credentials and authenticate the user.

        Args:
            data (dict): The data containing username/email and password.

        Returns:
            dict: The tokens for the authenticated user.

        Raises:
            UserNotFoundException: If the user cannot be found or is inactive.
        """
        username_or_email = data.get('username_or_email')
        password = data.get('password')

        user = authenticate(username=username_or_email, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                raise UserNotFoundException()

        if not user:
            raise UserNotFoundException()
        if not user.is_active:
            raise InactiveUserException()

        tokens = TokenMixin.get_tokens_for_user(user)
        return tokens