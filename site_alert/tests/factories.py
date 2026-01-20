import factory.django

from site_alert.models import SiteAlert, SiteAlertLevel


class SiteAlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SiteAlert

    is_active = True
    level = SiteAlertLevel.INFO
    message_en = factory.Faker("sentence")
    message_fi = ""
    message_sv = ""
