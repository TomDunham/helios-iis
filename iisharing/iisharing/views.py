from django.views.generic import ListView

from iisharing.models import Item

class StockView(ListView):
    model = Item
