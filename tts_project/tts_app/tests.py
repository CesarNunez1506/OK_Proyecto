from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from unittest.mock import patch, MagicMock, call
import json
import paho.mqtt.client as mqtt
from gestos.models import Gesto, Dedo
from django.core.files.storage import default_storage
import os
from tts_app.views import (  # Update this import path to match your project structure
    MqttToTtsView,
    process_data,
    handle_audio_complete,
    on_connect,
    on_message,
    TOPIC_SENSORES,
    TOPIC_COMPLETADO,
    is_playing,
    pending_message,
    last_message
)

class MqttToTtsTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test gesture and fingers
        self.gesto = Gesto.objects.create(significado="hola")
        fingers = {
            'pulgar': 90,
            'indice': 180,
            'medio': 180,
            'anular': 180,
            'menique': 180
        }
        for nombre, valor in fingers.items():
            Dedo.objects.create(gesto=self.gesto, nombre=nombre, valor=valor)
        
        # Sample valid gesture data
        self.valid_gesture_data = {
            'pulgar': 95,
            'indice': 175,
            'medio': 185,
            'anular': 178,
            'menique': 182
        }

        # Ensure media directory exists
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)

    @patch('paho.mqtt.client.Client')
    def test_mqtt_client_setup(self, mock_client):
        """Test MQTT client initialization and connection"""
        # Re-import to trigger client setup
        with patch('tts_app.views.mqtt.Client', return_value=mock_client):
            from importlib import reload
            import tts_app.views
            reload(tts_app.views)
            
            # Verify client configuration
            mock_client.username_pw_set.assert_called_once_with(
                "Kevin-parse", "20241506"
            )
            mock_client.tls_set.assert_called_once()
            mock_client.connect.assert_called_once_with(
                "p5d4eb0f.ala.eu-central-1.emqxsl.com", 8883
            )

    @patch('gtts.gTTS')
    @patch('paho.mqtt.client.Client')
    def test_process_data_valid_gesture(self, mock_client, mock_gtts):
        """Test processing valid gesture data"""
        # Setup mock for gTTS
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        
        # Process valid gesture data
        with patch('tts_app.views.client', mock_client):
            process_data(json.dumps(self.valid_gesture_data))
        
            # Verify TTS was called with correct parameters
            mock_gtts.assert_called_once_with("hola", lang='es')
            mock_tts_instance.save.assert_called_once()
            
            # Verify MQTT messages were published
            expected_calls = [
                call('/sensores/parse', 'hola'),
                call('/datos/api', f'http://192.168.15.15:8000/media/hola.mp3')
            ]
            mock_client.publish.assert_has_calls(expected_calls, any_order=True)

    def test_process_data_invalid_json(self):
        """Test processing invalid JSON data"""
        with self.assertLogs(level='ERROR') as log:
            process_data("invalid json")
            self.assertIn('Error al decodificar el mensaje JSON', log.output[0])

    def test_process_data_missing_fingers(self):
        """Test processing data with missing finger values"""
        invalid_data = {
            'pulgar': 90,
            'indice': 180
            # Missing other fingers
        }
        
        with self.assertLogs(level='ERROR') as log:
            process_data(json.dumps(invalid_data))
            self.assertIn('Datos incompletos recibidos', log.output[0])

    @patch('tts_app.views.client')
    def test_handle_audio_complete(self, mock_client):
        """Test handling of audio completion"""
        global is_playing, pending_message
        
        # Set initial state
        is_playing = True
        pending_message = json.dumps(self.valid_gesture_data)
        
        # Handle audio complete
        handle_audio_complete()
        
        # Verify state changes
        self.assertFalse(is_playing)
        self.assertIsNone(pending_message)

    def test_mqtt_view_no_message(self):
        """Test MqttToTtsView when no message is available"""
        global last_message
        last_message = None
        
        view = MqttToTtsView()
        response = view.get(None)
        
        self.assertEqual(
            response.json(),
            {"status": "Esperando un mensaje en el tópico MQTT"}
        )

    @patch('tts_app.views.process_data')
    def test_mqtt_view_with_message(self, mock_process):
        """Test MqttToTtsView when a message is available"""
        global last_message
        
        # Set up test message
        last_message = json.dumps(self.valid_gesture_data)
        
        view = MqttToTtsView()
        response = view.get(None)
        
        mock_process.assert_called_once_with(last_message)

    def test_gesture_matching_with_tolerance(self):
        """Test gesture matching with tolerance margins"""
        edge_case_data = {
            'pulgar': 119,
            'indice': 209,
            'medio': 209,
            'anular': 209,
            'menique': 209
        }
        
        with patch('gtts.gTTS') as mock_gtts:
            process_data(json.dumps(edge_case_data))
            mock_gtts.assert_called_once_with("hola", lang='es')

    def tearDown(self):
        """Clean up after tests"""
        # Clean up any created audio files
        test_audio_path = os.path.join(settings.MEDIA_ROOT, "hola.mp3")
        if os.path.exists(test_audio_path):
            os.remove(test_audio_path)

class MqttCallbackTests(TestCase):
    def setUp(self):
        self.client = mqtt.Client()
        
    def test_on_connect_success(self):
        """Test successful MQTT connection callback"""
        with self.assertLogs(level='INFO') as log:
            on_connect(self.client, None, None, 0)
            self.assertIn('Conectado al broker MQTT', log.output[0])
    
    def test_on_connect_failure(self):
        """Test failed MQTT connection callback"""
        with self.assertLogs(level='ERROR') as log:
            on_connect(self.client, None, None, 1)
            self.assertIn('Error de conexión: 1', log.output[0])

    @patch('tts_app.views.process_data')
    def test_on_message_sensor_topic(self, mock_process):
        """Test message handling for sensor topic"""
        global is_playing
        
        # Create mock message
        mock_msg = MagicMock()
        mock_msg.topic = TOPIC_SENSORES
        mock_msg.payload = b'{"test": "data"}'
        
        # Test when not playing
        is_playing = False
        on_message(self.client, None, mock_msg)
        mock_process.assert_called_once_with('{"test": "data"}')
        
        # Test when playing
        is_playing = True
        on_message(self.client, None, mock_msg)
        self.assertEqual(mock_process.call_count, 1)  # Should not have been called again

    def test_on_message_complete_topic(self):
        """Test message handling for completion topic"""
        global is_playing
        
        # Set initial state
        is_playing = True
        
        # Create mock message
        mock_msg = MagicMock()
        mock_msg.topic = TOPIC_COMPLETADO
        mock_msg.payload = b'completed'
        
        on_message(self.client, None, mock_msg)
        self.assertFalse(is_playing)