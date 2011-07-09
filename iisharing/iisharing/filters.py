import django_filters

from iisharing.models import Item

class ProductFilterSet(django_filters.FilterSet):
    class Meta:
        model = Item
        fields = ['shared_code', 'organization']
