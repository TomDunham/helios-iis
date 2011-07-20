from django.contrib import admin

from iisharing.models import Organisation
from iisharing.models import Item
from iisharing.models import UnitOfMeasure
from iisharing.models import Country

class ItemAdmin(admin.ModelAdmin):
    list_display = ('code_share', 'country','code_org', 
                    'description', 'quantity', 'uom', 
                    'organisation', 'status', 'date')

admin.site.register(Organisation)
admin.site.register(UnitOfMeasure)
admin.site.register(Country)
admin.site.register(Item, ItemAdmin)
