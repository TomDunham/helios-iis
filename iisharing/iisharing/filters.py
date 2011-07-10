import django_filters

from iisharing.models import Item, Country, Organization, STATUS_CHOICES

class StockFilterSet(django_filters.FilterSet):
    country = django_filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all())

    organization = django_filters.ModelMultipleChoiceFilter(
        queryset=Organization.objects.all())

    status = django_filters.MultipleChoiceFilter(
        choices = STATUS_CHOICES)


    class Meta:
        model = Item
        fields = ['country', 'shared_code', 'organization', 'status']
