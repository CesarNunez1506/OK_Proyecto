from rest_framework import serializers # type: ignore
from .models import Gesto

class GestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gesto
        fields = ['id', 'significado']  # Solo permite actualizar el campo significado
        read_only_fields = ['dedos']  # Los dedos serán de solo lectura para evitar su modificación
