from rest_framework import serializers

class PalabraSerializer(serializers.Serializer):
    palabra = serializers.CharField(max_length=100)
    audio_url = serializers.URLField()
