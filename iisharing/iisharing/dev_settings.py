from settings import *
import autofixture
autofixture.autodiscover()


INSTALLED_APPS += (
    'autofixture',
    )

