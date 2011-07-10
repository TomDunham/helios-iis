import django_filters

from iisharing.models import Item

class StockFilterSet(django_filters.FilterSet):
    class Meta:
        model = Item
        fields = ['country', 'shared_code', 'organization']
