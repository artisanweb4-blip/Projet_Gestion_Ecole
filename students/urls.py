from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # ⚠️ La route principale de la liste doit être '' et non 'list/' ou 'students/'
    path('', views.StudentListView.as_view(), name='list'),
    path('add/', views.StudentCreateView.as_view(), name='add'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
]