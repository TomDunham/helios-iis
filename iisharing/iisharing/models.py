from django.db import models

class Country(models.Model):
    """
    UN country (location) codes.

    See:
    http://live.unece.org/cefact/codesfortrade/codes_index.html
    http://live.unece.org/cefact/locode/welcome.html
    """
    code = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.code)


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


STATUS_CHOICES = (
    ('STOCK', 'STOCK'),
    ('ORDERED', 'ORDERED'),
)

class Item(models.Model):
    shared_code = models.CharField(
        max_length=32,
        help_text = "Cross-organization item code")
    org_code = models.CharField(
        max_length=32,
        help_text="Organization-specfific item code")
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    unit_of_measure = models.ForeignKey(UnitOfMeasure)
    organization = models.ForeignKey(Organization)
    status = models.CharField(
        choices = STATUS_CHOICES,
        max_length = 10)
    country = models.ForeignKey(Country)


