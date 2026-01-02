from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction

from .serializers import UserRegisterSerializer, UserProfileSerializer
from client.models import Client

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer


class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        email = request.data.get('email')
        if Client.objects.filter(contact_email=email).exists():
            return Response({"error": "This email is already registered."}, status=400)
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        company_name = request.data.get('company_name')
        if not company_name:
            return Response(
                {"company_name": "This field is required."},
                status=400
            )

        user = serializer.save()

        # ✅ Safe client creation
        Client.objects.create(
            user=user,
            company_name=company_name,
            contact_email=user.email
        )

        return Response(
            {"message": "Client registered successfully"},
            status=201
        )


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
