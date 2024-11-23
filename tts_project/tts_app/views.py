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
TOPIC_COMPLETADO = "/datos/completado"

# Último mensaje recibido y cola de mensajes pendientes
last_message = None
pending_message = None

# Bandera para controlar el estado de reproducción del ESP32
is_playing = False

# Configura una única instancia del cliente MQTT
client = mqtt.Client()
client.username_pw_set(MQTT_USER_BACKEND, MQTT_PASSWORD_BACKEND)
client.tls_set(CERTIFICATE_PATH)

# Callback de conexión
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Conectado al broker MQTT")
        # Suscripción a los tópicos
        client.subscribe([(TOPIC_SENSORES, 0), (TOPIC_COMPLETADO, 0)])
    else:
        logging.error(f"Error de conexión: {rc}")

# Callback de mensaje recibido
def on_message(client, userdata, msg):
    global last_message, is_playing, pending_message
    last_message = msg.payload.decode()
    logging.info(f"Mensaje recibido en {msg.topic}: {last_message}")

    # Procesar mensajes según el tópico
    if msg.topic == TOPIC_SENSORES:
        if not is_playing:
            process_data(last_message)
        else:
            # Guardar el mensaje como pendiente si ya se está reproduciendo un audio
            pending_message = last_message
            logging.info("Reproducción en curso. Mensaje guardado en cola.")

    elif msg.topic == TOPIC_COMPLETADO:
        handle_audio_complete()

# Configura el cliente MQTT solo una vez
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()  # Ejecuta el loop en segundo plano

# Funciones de procesamiento de datos y publicación

def process_data(data):
    global is_playing
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
        margen_tolerancia = 20  # Ajusta este valor según sea necesario

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

            # Asegurarse de que el nombre del archivo sea seguro para URLs
            # Reemplazar espacios por guiones bajos y eliminar caracteres problemáticos
            safe_significado = significado.replace(" ", "_").replace("/", "_")  # Reemplaza espacios y barras por guiones bajos
            audio_file_name = f"{safe_significado}.mp3"  # Nombre del archivo sin espacios
            audio_path = os.path.join(settings.MEDIA_ROOT, audio_file_name)
            tts.save(audio_path)

            # Imprimir el nombre del archivo guardado
            logging.info(f"Archivo de audio guardado: {audio_path}")

            # Publicar la palabra procesada en el tópico /sensores/parse
            publish_to_parse(significado)

            # Generar la URL del archivo TTS
            audio_url = f"http://192.168.152.49:8000/media/{audio_file_name}"  # Cambia localhost:8000 por la URL correcta
            publish_audio_url(audio_url)  # Publicar la URL en el tópico /datos/api

            # Establecer que se está reproduciendo un audio
            is_playing = True

        else:
            logging.info("No se encontró ningún gesto que coincida con los valores recibidos.")

    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar el mensaje JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Error al procesar los datos: {e}")

def handle_audio_complete():
    global is_playing, pending_message
    logging.info("Reproducción completada. El ESP32 está disponible para un nuevo audio.")
    is_playing = False  # Resetear la bandera para permitir una nueva reproducción

    # Si hay un mensaje pendiente en cola, procesarlo ahora
    if pending_message:
        logging.info("Procesando mensaje pendiente en cola.")
        process_data(pending_message)
        pending_message = None

def publish_to_parse(significado):
    client.publish(TOPIC_PARSE, significado)
    logging.info(f"Significado del gesto publicado en /sensores/parse: {significado}")

def publish_audio_url(audio_url):
    client.publish(TOPIC_API, audio_url)
    logging.info(f"URL del audio publicada en /datos/api: {audio_url}")

# Vista para interactuar con el cliente MQTT
class MqttToTtsView(View):

    def get(self, request):
        global last_message
        if last_message:
            response = process_data(last_message)
            return response if response else JsonResponse({"status": "No se encontró un gesto."})
        else:
            return JsonResponse({"status": "Esperando un mensaje en el tópico MQTT"})
