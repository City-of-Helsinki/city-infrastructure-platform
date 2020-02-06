import csv
import os

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from django.utils.crypto import get_random_string

from users.models import User


class Command(BaseCommand):
    help = "Import traffic sign code data from a csv file"

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to the traffic sign codes csv file")

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError("File {0} does not exist".format(filename))

        with open(filename, mode="r", encoding="utf-8-sig") as csv_file:
            username = get_random_string()
            password = get_random_string()
            user = User.objects.create_superuser(
                username=username, password=password, email="testadmin@example.com"
            )
            client = Client()
            client.login(username=username, password=password)
            csv_reader = csv.DictReader(csv_file, delimiter=";")
            counter = 0
            for row in csv_reader:
                code = row["MerkkiKoodi"].strip()
                description = row["Kuvaus"].strip()
                data = {"code": code, "description": description}
                self.stdout.write(
                    "Importing Traffic Sign Code: {0} - {1}".format(code, description)
                )
                client.post(reverse("api:trafficsigncode-list"), data, format="json")
                counter += 1
            user.delete()

        self.stdout.write("{0} objects are imported".format(counter))
