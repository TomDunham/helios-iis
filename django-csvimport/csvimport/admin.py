from datetime import datetime

from django.contrib import admin
from django.contrib.admin import ModelAdmin 

from csvimport.models import CSVImport

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
        from csvimport.management.commands.csvimport import Command
        cmd = Command()
        if obj.upload_file:
            obj.file_name = obj.upload_file.name
            obj.encoding = ''
            defaults = self.filename_defaults(obj.file_name)
            cmd.setup(mappings=obj.field_list, 
                      modelname=obj.model_name, 
                      uploaded=obj.upload_file,
                      defaults=defaults)
        errors = cmd.run(logid=obj.id)
        if errors:
            obj.error_log = '\n'.join(errors)
        obj.import_user = str(request.user)
        obj.import_date = datetime.now()
        obj.save()

    def filename_defaults(self, filename):
        """ Override this method to supply filename based data """
        # example ORG-COUNTRY.csv
        defaults = []
        if filename.find('.')>-1:
            name = filename.split('.')[0]
            if name.find('_')>-1:
                name = name.split('_')[0]
            try:
                org, country = name.split('-')
            except:
                return defaults
            if org:
                defaults.append(('code_org', org, ('Organisation', 'name')))
            if country:
                defaults.append(('country', country, ('Country', 'code')))
        return defaults

admin.site.register(CSVImport, CSVImportAdmin)
