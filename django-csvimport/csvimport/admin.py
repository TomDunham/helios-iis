from datetime import datetime

from django.contrib import admin
from django.contrib.admin import ModelAdmin 

from csvimport.models import CSVImport
from csvimport.management.commands.csvimport import Command

class CSVImportAdmin(ModelAdmin):
    ''' Custom model to not have much editable! '''
    readonly_fields = ['file_name',
                       'encoding',
                       'upload_method',
                       'error_log',
                       'import_user']

    def save_model(self, request, obj, form, change):
        """ Do save and process command - cant commit False
            since then file wont be found for reopening via right charset
        """
        form.save()
        cmd = Command()
        if obj.upload_file:
            obj.file_name = obj.upload_file.name
            obj.encoding = ''
            cmd.setup(mappings=obj.field_list, 
                      modelname=obj.model_name, 
                      uploaded=obj.upload_file)
        errors = cmd.run()
        obj.error_log = '\n'.join(errors)
        obj.import_user = str(request.user)
        obj.import_date = datetime.now()
        obj.save()

       


admin.site.register(CSVImport, CSVImportAdmin)
