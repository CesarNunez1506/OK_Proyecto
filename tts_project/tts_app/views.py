from django.views import View
import os
import logging
import paho.mqtt.client as mqtt
from django.http import JsonResponse, FileResponse
from django.conf import settings
from gtts import gTTS
from gestos.models import Gesto   # Asegúrate de importar tu modelo Gesto
import json

# Configuración de logs
logging.basicConfig(level=logging.DEBUG)

# Variables de conexión MQTT
MQTT_BROKER = "p5d4eb0f.ala.eu-central-1.emqxsl.com"  
MQTT_PORT = 8883
MQTT_USER = "Kevin-parse"
MQTT_PASSWORD = "20241506"
TOPIC = "/sensores/abc"
CERTIFICATE_PATH = "C:/Users/ASUS/Desktop/OK/OK_Proyecto/tts_project/mqtt_cert.pem"

# Almacena el último mensaje recibido
last_message = None

# Función para configurar el cliente MQTT
def setup_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set(CERTIFICATE_PATH)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Conectado al broker MQTT")
            client.subscribe(TOPIC)
        else:
            logging.error(f"Error de conexión: {rc}")

    def on_message(client, userdata, msg):
        global last_message
        last_message = msg.payload.decode()
        logging.info(f"Último mensaje recibido: {last_message}")

        # Procesar los datos al recibir un nuevo mensaje
        process_data(last_message)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    return client

def process_data(data):
    try:
        # Convertir el mensaje en JSON
        received_data = json.loads(data)  # Espera un JSON con los valores de los dedos
        
        # Extraer los valores
        pulgar_valor = received_data.get('pulgar')
        indice_valor = received_data.get('indice')
        medio_valor = received_data.get('medio')
        anular_valor = received_data.get('anular')
        menique_valor = received_data.get('menique')

        # Validación de datos
        if None in (pulgar_valor, indice_valor, medio_valor, anular_valor, menique_valor):
            logging.error("Datos incompletos recibidos.")
            return
        
        # Buscar gesto en la base de datos
        matching_gestos = Gesto.objects.filter(
            dedos__nombre='pulgar', dedos__valor=pulgar_valor
        ).filter(
            dedos__nombre='indice', dedos__valor=indice_valor
        ).filter(
            dedos__nombre='medio', dedos__valor=medio_valor
        ).filter(
            dedos__nombre='anular', dedos__valor=anular_valor
        ).filter(
            dedos__nombre='menique', dedos__valor=menique_valor
        ).distinct()

        if matching_gestos.exists():
            gesto = matching_gestos.first()  # Obtener el primer gesto que coincide
            significado = gesto.significado
            logging.info(f"Gesto encontrado: {significado}")

            # Conversión a audio
            tts = gTTS(significado, lang='es')
            audio_path = os.path.join(settings.MEDIA_ROOT, "output.mp3")
            tts.save(audio_path)

            # Opción para eliminar el archivo después de enviar la respuesta
            # os.remove(audio_path)

            return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg')
        else:
            logging.info("No se encontró ningún gesto que coincida con los valores recibidos.")

    except Exception as e:
        logging.error(f"Error al procesar los datos: {e}")

class MqttToTtsView(View):
    client = setup_mqtt()  # Mantener el cliente conectado

    def get(self, request):
        global last_message
        if last_message:
            return process_data(last_message)
        else:
            return JsonResponse({"status": "Esperando un mensaje en el tópico MQTT"})
