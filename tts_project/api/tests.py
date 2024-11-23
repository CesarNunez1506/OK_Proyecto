from django.test import TestCase

from rest_framework import status
from django.urls import reverse
from rest_framework.test import APIClient

class PalabraViewTestCase(TestCase):
    
    def setUp(self):
        # Establecemos el cliente para hacer las solicitudes API
        self.client = APIClient()
        self.url = reverse('obtener_palabra_y_audio')

    def test_obtener_palabra_y_audio_success(self):
        # Realizamos una solicitud GET a la vista
        response = self.client.get(self.url)
        
        # Verificamos que la respuesta sea 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificamos que los datos que devuelve la vista sean los esperados
        expected_data = {
            'palabra': 'Hola',
            'audio_url': 'http://backend_ip/media/audio/hola.mp3'
        }
        
        self.assertEqual(response.data, expected_data)

    def test_obtener_palabra_y_audio_invalid_method(self):
        # Hacemos una solicitud con un método no permitido (POST en este caso)
        response = self.client.post(self.url)
        
        # La vista solo permite GET, por lo que debe retornar un error 405 Method Not Allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)