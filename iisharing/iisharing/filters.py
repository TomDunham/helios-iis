import django_filters

from iisharing.models import Item, Country, Organization

class StockFilterSet(django_filters.FilterSet):
    country = django_filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all())

    organization = django_filters.ModelMultipleChoiceFilter(
        queryset=Organization.objects.all())

    class Meta:
        model = Item
        fields = ['country', 'shared_code', 'organization', 'status']

    def __init__(self, *args, **kwargs):
        super(StockFilterSet, self).__init__(*args, **kwargs)
        istatus = Item.objects.values_list('status', flat=True).distinct()
        status = django_filters.MultipleChoiceFilter(
            name = "status",
            choices = [(s, s) for s in istatus]
            )
        self.filters['status'] = status
