import django_filters

from iisharing.models import Item, Country, Organisation

class StockFilterSet(django_filters.FilterSet):
    country = django_filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all())

    organisation = django_filters.ModelMultipleChoiceFilter(
        queryset=Organisation.objects.all())

    class Meta:
        model = Item
        fields = ['country', 'code_share', 'organisation', 'status']

    def __init__(self, *args, **kwargs):
        super(StockFilterSet, self).__init__(*args, **kwargs)
        istatus = Item.objects.values_list('status', flat=True).distinct()
        status = django_filters.MultipleChoiceFilter(
            name = "status",
            choices = [(s, s) for s in istatus]
            )
        self.filters['status'] = status
