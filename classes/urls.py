# classes/urls.py
from django.urls import path
from . import views

app_name = 'classes'  # Déclare l'espace de noms 'classes'

urlpatterns = [
    path('', views.ClassListView.as_view(), name='list'),
    path('add/', views.ClassCreateView.as_view(), name='add'),
    path('<int:pk>/', views.ClassDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClassUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ClassDeleteView.as_view(), name='delete'),
]