from django.contrib import admin

from iisharing.models import Organization
from iisharing.models import Item
from iisharing.models import UnitOfMeasure
from iisharing.models import Country

class ItemAdmin(admin.ModelAdmin):
    list_display = ('shared_code', 'org_code', 'description', 'quantity', 'unit_of_measure', 'organization', 'status')

admin.site.register(Organization)
admin.site.register(UnitOfMeasure)
admin.site.register(Country)
admin.site.register(Item, ItemAdmin)
