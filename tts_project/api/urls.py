from django.urls import path
from . import views

urlpatterns = [
    path('api/obtener_palabra_y_audio/', views.obtener_palabra_y_audio, name='obtener_palabra_y_audio'),
]
