from django.views import View
import os
import logging
import paho.mqtt.client as mqtt
from django.http import JsonResponse, FileResponse
from django.conf import settings
from gtts import gTTS

# Configuración de logs
logging.basicConfig(level=logging.DEBUG)

# Variables de conexión MQTT
MQTT_BROKER = "p5d4eb0f.ala.eu-central-1.emqxsl.com"  # Cambia según tu configuración
MQTT_PORT = 8883  # Cambia según tu broker
MQTT_USER = "Kevin-parse"
MQTT_PASSWORD = "20241506"
TOPIC = "/sensores/abc"
CERTIFICATE_PATH = "C:\\Django\\Tts\\tts_project\\mqtt_cert.pem"

# Almacena el último mensaje recibido
last_message = None

class MqttToTtsView(View):
    def get(self, request):
        global last_message
        client = mqtt.Client()

        # Configura la autenticación
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

        # Configura TLS
        client.tls_set(CERTIFICATE_PATH)

        # Función callback cuando el cliente se conecta al broker
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info("Conectado al broker MQTT")
                client.subscribe(TOPIC)
            else:
                logging.error(f"Error de conexión: {rc}")

        # Función callback para recibir mensajes
        def on_message(client, userdata, msg):
            global last_message
            last_message = msg.payload.decode()
            logging.info(f"Último mensaje recibido: {last_message}")

        client.on_connect = on_connect
        client.on_message = on_message

        try:
            # Conectar al broker
            client.connect(MQTT_BROKER, MQTT_PORT)
            client.loop_start()  # Inicia el bucle para procesar mensajes

            # Espera a que se reciba un mensaje
            if last_message:
                # Convierte el último mensaje en audio usando gTTS
                tts = gTTS(last_message, lang='es')
                audio_path = os.path.join(settings.MEDIA_ROOT, "output.mp3")
                tts.save(audio_path)

                # Retorna el archivo de audio como respuesta
                return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg')
            else:
                return JsonResponse({"status": "Esperando un mensaje en el tópico MQTT"})

        except Exception as e:
            logging.error(f"Error en la conexión MQTT o TTS: {e}")
            return JsonResponse({"status": "Error", "error": str(e)})