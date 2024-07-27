from django.urls import path
from . import views

urlpatterns = [
    path('create-order/', views.CreateOrderView.as_view(), name='create-order'),
    path('verify-payment/', views.VerifyPaymentView.as_view(), name='verify-payment'),
    path('',views.payment_form,name='index'),
]