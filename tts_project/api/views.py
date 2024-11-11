from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import PalabraSerializer

@api_view(['GET'])
def obtener_palabra_y_audio(request):
    if request.method == 'GET':
        # Aquí llamamos las funciones que ya tienes implementadas para generar la palabra y el archivo TTS
        palabra_procesada = "Hola"  # Esto debe provenir del procesamiento del backend
        url_audio = "http://backend_ip/media/audio/hola.mp3"  # URL donde está guardado el archivo TTS

        # Serializar los datos
        serializer = PalabraSerializer(data={
            'palabra': palabra_procesada,
            'audio_url': url_audio
        })

        # Validar y retornar la respuesta
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)
