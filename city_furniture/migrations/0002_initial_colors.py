# Generated by Django 2.2.26 on 2022-02-02 09:56

from django.db import migrations


def create_initial_owners(apps, schema_editor):
    CityFurnitureColor = apps.get_model("city_furniture", "CityFurnitureColor")

    initial_colors = (
        # refs. https://brand.hel.fi/en/colours/
        ("Coat of Arms", "#0072C6"),
        ("Gold", "#C2A251"),
        ("Silver", "#DEDFE1"),
        ("Brick", "#BD2719"),
        ("Bus", "#0000BF"),
        ("Copper", "#00D7A7"),
        ("Engel", "#FFE977"),
        ("Fog", "#9FC9EB"),
        ("Metro", "#FD4F00"),
        ("Summer", "#FFC61E"),
        ("Suomenlinna", "#F5A3C7"),
        ("Tram", "#008741"),
        # refs. https://kaupunkitilaohje.hel.fi/kortti/rantareittien-opastus/
        ("Kantakaupunki", "#C2A251"),
        ("Seurasaarenselkä", "#A6E6FF"),
        ("Lauttasaari", "#FF8CFF"),
        ("Kruunuvuorenselkä", "#FFFFFF"),
        ("Vanhankaupunginlahti", "#59FF66"),
        ("Laajasalo", "#F2FF59"),
        ("Itäinen Helsinki", "#FF9980"),
    )

    for name, rgb in initial_colors:
        CityFurnitureColor.objects.get_or_create(name=name, defaults=dict(rgb=rgb))

class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0001_initial_city_furniture'),
    ]

    operations = [
        migrations.RunPython(create_initial_owners, reverse_code=migrations.RunPython.noop),
    ]