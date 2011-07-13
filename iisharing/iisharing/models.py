from django.db import models
from csvimport.models import CSVImport

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


class Organisation(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Item(models.Model):
    TYPE = models.PositiveIntegerField(default=0)
    code_share = models.CharField(
        max_length=32,
        help_text = "Cross-organization item code")
    code_org = models.CharField(
        max_length=32,
        help_text="Organization-specfific item code")
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    uom = models.ForeignKey(UnitOfMeasure,
                            help_text = 'Unit of Measure')
    organisation = models.ForeignKey(Organisation)
    status = models.CharField(max_length = 10)
    date = models.DateField(auto_now=True)
    country = models.ForeignKey(Country)


