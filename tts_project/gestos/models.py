from django.db import models

# Modelo para representar un dedo
class Dedo(models.Model):
    NOMBRE_DEDO_CHOICES = [
        ('pulgar', 'Pulgar'),
        ('indice', 'Índice'),
        ('medio', 'Medio'),
        ('anular', 'Anular'),
        ('menique', 'Meñique'),
    ]
    
    nombre = models.CharField(max_length=10, choices=NOMBRE_DEDO_CHOICES)
    valor = models.IntegerField()

    def __str__(self):
        return f"{self.nombre}: {self.valor}"

# Modelo para representar un gesto completo
class Gesto(models.Model):
    dedos = models.ManyToManyField(Dedo)  # Relación muchos a muchos con Dedo
    significado = models.CharField(max_length=100)

    def __str__(self):
        return f"Gesto: {self.significado}"

    def get_dedos_valores(self):
        return ", ".join([f"{dedo.nombre}: {dedo.valor}" for dedo in self.dedos.all()])
