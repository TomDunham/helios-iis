from django.contrib import admin

from iisharing.models import Organization
from iisharing.models import Item
from iisharing.models import UnitOfMeasure

admin.site.register(Organization)
admin.site.register(UnitOfMeasure)
admin.site.register(Item)
