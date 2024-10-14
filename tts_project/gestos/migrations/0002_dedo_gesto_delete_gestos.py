# Generated by Django 5.1.1 on 2024-10-14 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dedo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(choices=[('pulgar', 'Pulgar'), ('indice', 'Índice'), ('medio', 'Medio'), ('anular', 'Anular'), ('menique', 'Meñique')], max_length=10)),
                ('valor', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Gesto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('significado', models.CharField(max_length=100)),
                ('dedos', models.ManyToManyField(to='gestos.dedo')),
            ],
        ),
        migrations.DeleteModel(
            name='Gestos',
        ),
    ]