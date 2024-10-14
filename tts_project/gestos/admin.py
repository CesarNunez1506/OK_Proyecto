from django.contrib import admin
from .models import Dedo, Gesto

@admin.register(Dedo)
class DedoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'valor')

# Registro de Gesto en el admin
@admin.register(Gesto)
class GestoAdmin(admin.ModelAdmin):
    list_display = ('significado', 'get_dedos_valores')
    filter_horizontal = ('dedos',)