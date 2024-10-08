import paho.mqtt.client as mqtt
import pyttsx3
import os
from django.conf import settings

# Inicializar el motor de pyttsx3
engine = pyttsx3.init()

# Configurar el cliente MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado con código de resultado: " + str(rc))
    client.subscribe("/sensores/abc")

def on_message(client, userdata, msg):
    text = msg.payload.decode()  # Decodificar el mensaje recibido
    print(f"Mensaje recibido: {text}")
    
    # Generar audio a partir del texto recibido
    audio_file = os.path.join(settings.MEDIA_ROOT, 'output.mp3')
    engine.save_to_file(text, audio_file)
    engine.runAndWait()

# Configuración del cliente MQTT
client = mqtt.Client()
client.username_pw_set("Kevin", "20241506")  # Usuario y contraseña
client.on_connect = on_connect
client.on_message = on_message

# Conectar al broker MQTT
client.connect("p5d4eb0f.ala.eu-central-1.emqxsl.com", 8883, 60)  # Cambia esto por tu broker
client.loop_start()  # Inicia el bucle del cliente MQTT
