from autofixture import generators, register, AutoFixture

from iisharing.models import Item


class StockAutoFixture(AutoFixture):
    field_values = {
        'description': generators.LoremGenerator(max_length=100),
        'shared_code': generators.ChoicesGenerator(
            choices=(
                ('TENT', 'TENT'),
                ('CEMENT', 'CEMENT'),
                ('FOO', 'FOO'),
                )
            )
    }

register(Item, StockAutoFixture)
