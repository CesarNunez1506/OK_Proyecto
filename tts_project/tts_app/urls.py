# tts_app/urls.py
from django.urls import path
from .views import MqttToTtsView

urlpatterns = [
    path('mqtt/connect/', MqttToTtsView.as_view(), name='mqtt_connect'),
]
