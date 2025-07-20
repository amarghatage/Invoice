from django.urls import path
from .import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('new/', views.invoice_create_update, name='invoice_create'),
    path('<int:pk>/edit/', views.invoice_create_update, name='invoice_edit'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
