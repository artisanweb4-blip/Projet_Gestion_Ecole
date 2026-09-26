from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeStructureViewSet, StudentPaymentViewSet

router = DefaultRouter()
router.register(r'fees', FeeStructureViewSet, basename='fee')
router.register(r'payments', StudentPaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
