import factory.django

from site_alert.models import SiteAlert


class SiteAlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteAlert

    is_active = True
    level = "info"
    message_en = factory.Faker("sentence")
    message_fi = ""
    message_sv = ""
