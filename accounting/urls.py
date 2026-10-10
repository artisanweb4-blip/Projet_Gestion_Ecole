from django.urls import path

from . import views

app_name = 'accounting'

urlpatterns = [
    path('', views.AccountingIndexView.as_view(), name='index'),

    # Frais de scolarité PAR NIVEAU (grille officielle)
    path('tuitions/', views.TuitionListView.as_view(), name='tuitions'),
    path('tuitions/add/', views.TuitionCreateView.as_view(), name='tuition_add'),
    path('tuitions/<int:pk>/edit/', views.TuitionUpdateView.as_view(), name='tuition_edit'),
    path('tuitions/<int:pk>/delete/', views.TuitionDeleteView.as_view(), name='tuition_delete'),

    # Paiements (par élève ou par classe) + reçu A5
    path('payments/', views.PaymentListView.as_view(), name='payments'),
    path('payments/add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/receipt/', views.PaymentReceiptPDFView.as_view(), name='payment_receipt'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    path('payments/ajax/tuition/', views.PaymentTuitionAjaxView.as_view(), name='payment_tuition_ajax'),

    # Dépenses par catégorie (filtrables par mois)
    path('expenses/', views.ExpenseListView.as_view(), name='expenses'),
    path('expenses/add/', views.ExpenseCreateView.as_view(), name='expense_add'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),

    # Tranches & échéances (historique)
    path('fees/', views.FeeListView.as_view(), name='fees'),
    path('fees/add/', views.FeeCreateView.as_view(), name='fee_add'),
    path('fees/<int:pk>/edit/', views.FeeUpdateView.as_view(), name='fee_edit'),
    path('fees/<int:pk>/delete/', views.FeeDeleteView.as_view(), name='fee_delete'),
]
