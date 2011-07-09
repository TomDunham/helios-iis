from django.views.generic import ListView

from iisharing.models import Item
from iisharing.filters import StockFilterSet

class StockView(ListView):
    model = Item

    def get_context_data(self, **kwargs):
        ctx = super(StockView, self).get_context_data(**kwargs)
        ctx.update(filter = StockFilterSet(self.request.GET or None))
        return ctx

