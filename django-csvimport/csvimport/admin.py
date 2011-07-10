from django.contrib import admin
from django.contrib.admin import ModelAdmin 

from csvimport.models import CSVImport

class CSVImportAdmin(ModelAdmin):
    ''' Custom model to not have much editable! '''
    readonly_fields = ['file_name',
                       'encoding',
                       'upload_method',
                       'error_log',
                       'import_date',
                       'import_user']

admin.site.register(CSVImport, CSVImportAdmin)
