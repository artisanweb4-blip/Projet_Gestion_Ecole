from django.contrib.auth.views import LoginView as DjangoLoginView

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer
)
from core.permissions import IsAdminUserRole

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """Endpoint de connexion JWT renvoyant le token et le profil complet."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """Endpoint d'inscription pour créer un compte utilisateur."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Endpoint permettant à l'utilisateur connecté de consulter/modifier son profil."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordResetView(APIView):
    """Endpoint pour réinitialiser le mot de passe d'un utilisateur."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Mot de passe réinitialisé avec succès."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD réservé à l'administrateur pour gérer l'ensemble des comptes utilisateurs."""
    serializer_class = UserSerializer
    permission_classes = [IsAdminUserRole]

    def get_queryset(self):
        # Isolation multi-écoles : évalué par requête
        user = self.request.user
        if user.is_superuser:
            return User.objects.all().order_by('-created_at')
        if getattr(user, 'school_id', None):
            return User.objects.filter(school_id=user.school_id).order_by('-created_at')
        return User.objects.filter(pk=user.pk)
    search_fields = ['username', 'first_name', 'last_name', 'email', 'role']
    filterset_fields = ['role', 'is_active']


class SchoolLoginView(DjangoLoginView):
    """Connexion : refuse les comptes d'une école suspendue et envoie le
    Super Admin directement sur son interface plateforme."""

    def get_success_url(self):
        user = getattr(self.request, 'user', None)
        if user is not None and user.is_superuser:
            from django.urls import reverse
            return reverse('platform_dashboard')
        return super().get_success_url()

    def form_valid(self, form):
        user = form.get_user()
        school = getattr(user, 'school', None)
        if school is not None and not school.is_active:
            form.add_error(
                None,
                "Cet établissement est actuellement suspendu. "
                "Merci de contacter l'administrateur de la plateforme."
            )
            return self.form_invalid(form)
        return super().form_valid(form)
