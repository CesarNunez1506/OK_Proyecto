from django.test import TestCase
import pytest
from .models import Gesto, Dedo

class DedoModelTest(TestCase):
    
    def setUp(self):
        # Creamos un Dedo para usar en las pruebas
        self.dedo = Dedo.objects.create(nombre='pulgar', valor=1)
    
    def test_crear_dedo(self):
        # Verificamos que el Dedo se haya creado correctamente
        self.assertEqual(self.dedo.nombre, 'pulgar')
        self.assertEqual(self.dedo.valor, 1)

class GestoModelTest(TestCase):
    
    def setUp(self):
        # Creamos un par de Dedos
        self.dedo1 = Dedo.objects.create(nombre='pulgar', valor=1)
        self.dedo2 = Dedo.objects.create(nombre='indice', valor=2)
        
        # Creamos un Gesto y asociamos los Dedos
        self.gesto = Gesto.objects.create(significado="Hola")
        self.gesto.dedos.set([])

    def test_crear_gesto(self):
        # Verificamos que el Gesto se haya creado correctamente
        self.assertEqual(self.gesto.significado, 'Saludo')
        self.assertEqual(self.gesto.dedos.count(), 2)

    def test_get_dedos_valores(self):
        # Verificamos que el método get_dedos_valores funcione correctamente
        expected_output = 'pulgar: 1, indice: 2'
        self.assertEqual(self.gesto.get_dedos_valores(), expected_output)