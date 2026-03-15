from django.urls import path
from . import views

urlpatterns = [
    path('whatsapp/', views.whatsapp_bot, name='whatsapp_bot'),
     path('sms/', views.sms_bot, name='sms_bot'),
]