from rest_framework import viewsets, status # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.decorators import action # type: ignore
from .models import Gesto
from .serializers import GestoSerializer

class GestoViewSet(viewsets.ModelViewSet):
    queryset = Gesto.objects.all()
    serializer_class = GestoSerializer

    def update(self, request, *args, **kwargs):
        # Permite la actualización del campo significado sin alterar dedos
        instance = self.get_object()
        instance.significado = request.data.get('significado', instance.significado)
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # Elimina un gesto completamente
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
