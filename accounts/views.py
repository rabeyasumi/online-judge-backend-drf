from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.authtoken.models import Token

from .serializers import (
    RegisterSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


def get_user_data(user):

    student = getattr(user, 'student_profile', None)

    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,

        'student': {
            'id': student.id,
            'name': student.name,
            'handle': student.handle,
        } if student else None
    }


# -----------------------------
# USER REGISTRATION
# -----------------------------

class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            student = serializer.save()

            token, created = Token.objects.get_or_create(
                user=student.user
            )

            return Response({

                'message': 'Registration successful.',

                'token': token.key,

                'user': get_user_data(student.user)

            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# -----------------------------
# USER LOGIN
# -----------------------------

class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:

            return Response({

                'error': 'Username and password are required.'

            }, status=status.HTTP_400_BAD_REQUEST)


        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:

            return Response({

                'error': 'Invalid username or password.'

            }, status=status.HTTP_401_UNAUTHORIZED)


        token, created = Token.objects.get_or_create(
            user=user
        )

        return Response({

            'message': 'Login successful.',

            'token': token.key,

            'user': get_user_data(user)

        }, status=status.HTTP_200_OK)


# -----------------------------
# USER LOGOUT
# -----------------------------

class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        Token.objects.filter(user=request.user).delete()

        return Response({

            'message': 'Logout successful.'

        }, status=status.HTTP_200_OK)


# -----------------------------
# CURRENT USER
# -----------------------------

class CurrentUserView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({

            'user': get_user_data(request.user)

        }, status=status.HTTP_200_OK)
    

class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)