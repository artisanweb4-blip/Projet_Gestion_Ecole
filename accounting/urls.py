from django.urls import path

from . import views

app_name = 'accounting'

urlpatterns = [
    path('', views.AccountingIndexView.as_view(), name='index'),

    path('fees/', views.FeeListView.as_view(), name='fees'),
    path('fees/add/', views.FeeCreateView.as_view(), name='fee_add'),
    path('fees/<int:pk>/edit/', views.FeeUpdateView.as_view(), name='fee_edit'),
    path('fees/<int:pk>/delete/', views.FeeDeleteView.as_view(), name='fee_delete'),

    path('payments/', views.PaymentListView.as_view(), name='payments'),
    path('payments/add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
]
