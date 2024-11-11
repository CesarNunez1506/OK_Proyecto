from django.views import View
from django.http import JsonResponse, FileResponse
from django.conf import settings
from gtts import gTTS
from gestos.models import Gesto
import os
import logging
import json
import paho.mqtt.client as mqtt

# Configuración de logs
logging.basicConfig(level=logging.INFO)

# Variables de conexión MQTT
MQTT_BROKER = "p5d4eb0f.ala.eu-central-1.emqxsl.com"
MQTT_PORT = 8883
MQTT_USER_BACKEND = "Kevin-parse"
MQTT_PASSWORD_BACKEND = "20241506"
CERTIFICATE_PATH = "C:/Users/ASUS/Desktop/OK/OK_Proyecto/tts_project/mqtt_cert.pem"

# Tópicos
TOPIC_SENSORES = "/sensores/abc"
TOPIC_PARSE = "/sensores/parse"
TOPIC_API = "/datos/api"

# Último mensaje recibido
last_message = None

# Configura una única instancia del cliente MQTT
client = mqtt.Client()
client.username_pw_set(MQTT_USER_BACKEND, MQTT_PASSWORD_BACKEND)
client.tls_set(CERTIFICATE_PATH)

# Callback de conexión
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Conectado al broker MQTT")
        # Suscripción a los tópicos
        client.subscribe([(TOPIC_SENSORES, 0), (TOPIC_PARSE, 0), (TOPIC_API, 0)])
    else:
        logging.error(f"Error de conexión: {rc}")

# Callback de mensaje recibido
def on_message(client, userdata, msg):
    global last_message
    last_message = msg.payload.decode()
    logging.info(f"Mensaje recibido en {msg.topic}: {last_message}")

    # Procesar mensajes según el tópico
    if msg.topic == TOPIC_SENSORES:
        process_data(last_message)
    elif msg.topic == TOPIC_PARSE:
        handle_parse_message(last_message)
    elif msg.topic == TOPIC_API:
        handle_api_message(last_message)

# Configura el cliente MQTT solo una vez
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()  # Ejecuta el loop en segundo plano

# Funciones de procesamiento de datos y publicación

def comparar_valores(lectura, valor_referencia, margen=15):
    """
    Verifica si la lectura está dentro del margen permitido del valor de referencia.
    """
    return abs(lectura - valor_referencia) <= margen

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

        # Definir el margen de tolerancia para la comparación
        margen_tolerancia = 10  # Ajusta este valor según sea necesario

        # Buscar gesto en la base de datos con tolerancia en los valores
        matching_gestos = Gesto.objects.all()
        matching_gestos = matching_gestos.filter(
            dedos__nombre='pulgar', dedos__valor__range=(
                pulgar_valor - margen_tolerancia, pulgar_valor + margen_tolerancia)
        ).filter(
            dedos__nombre='indice', dedos__valor__range=(
                indice_valor - margen_tolerancia, indice_valor + margen_tolerancia)
        ).filter(
            dedos__nombre='medio', dedos__valor__range=(
                medio_valor - margen_tolerancia, medio_valor + margen_tolerancia)
        ).filter(
            dedos__nombre='anular', dedos__valor__range=(
                anular_valor - margen_tolerancia, anular_valor + margen_tolerancia)
        ).filter(
            dedos__nombre='menique', dedos__valor__range=(
                menique_valor - margen_tolerancia, menique_valor + margen_tolerancia)
        ).distinct()

        if matching_gestos.exists():
            gesto = matching_gestos.first()  # Obtener el primer gesto que coincide
            significado = gesto.significado
            logging.info(f"Gesto encontrado: {significado}")

            # Conversión a audio
            tts = gTTS(significado, lang='es')
            audio_file_name = f"{significado}.mp3"  # Nombre del archivo
            audio_path = os.path.join(settings.MEDIA_ROOT, audio_file_name)
            tts.save(audio_path)

            # Imprimir el nombre del archivo guardado
            logging.info(f"Archivo de audio guardado: {audio_path}")

            # Publicar la palabra procesada en el tópico /sensores/parse
            publish_to_parse(significado)

            # Generar la URL del archivo TTS
            audio_url = f"http://192.168.15.15:8000/media/{audio_file_name}"  # Cambia localhost:8000 por la URL correcta
            publish_audio_url(audio_url)   # Publicar la URL en el tópico /datos/api

            return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg')
        else:
            logging.info("No se encontró ningún gesto que coincida con los valores recibidos.")

    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar el mensaje JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Error al procesar los datos: {e}")

def handle_parse_message(data):
    logging.info(f"Procesando mensaje de /sensores/parse: {data}")

def handle_api_message(data):
    logging.info(f"Procesando mensaje de /datos/api: {data}")

def publish_to_parse(significado):
    client.publish(TOPIC_PARSE, significado)

def publish_audio_url(audio_url):
    client.publish(TOPIC_API, audio_url)

# Vista para interactuar con el cliente MQTT
class MqttToTtsView(View):

    def get(self, request):
        global last_message
        if last_message:
            response = process_data(last_message)
            return response if response else JsonResponse({"status": "No se encontró un gesto."})
        else:
            return JsonResponse({"status": "Esperando un mensaje en el tópico MQTT"})
