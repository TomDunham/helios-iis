from django.views.generic import ListView

from iisharing.models import Item
from iisharing.filters import StockFilterSet

class StockView(ListView):
    model = Item
    paginate_by = 100

    def get_filterset(self):
        return StockFilterSet(self.request.GET or None)

    def get_queryset(self):
        return self.get_filterset().qs

    def get_context_data(self, **kwargs):
        ctx = super(StockView, self).get_context_data(**kwargs)
        ctx.update(form = self.get_filterset().form)
        return ctx

