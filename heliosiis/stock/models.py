from django.db import models

class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=32)

class Organization(models.Model):
    name = models.CharField(max_length=255)


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
        choices = Item.STATUS_CHOICES,
        max_len = 4)


