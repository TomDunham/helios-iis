# Send signals for emails etc
#from django.db.models.signals import pre_save
from csvimport.models import CSVImport
from csvimport.management.commands.csvimport import Command

def run_csv_import(**kwargs):
    """ Run the custom command to do the csv import
        After manually saving a file 
    """
    cmd = Command()
    f = kwargs.get('instance', None)
    f.file_name = f.upload_file.name
    f.encoding = ''
    if f:
        cmd.setup(mappings=f.field_list, 
                  modelname=f.model_name, 
                  uploaded=f.upload_file)
    errors = cmd.run()
    f.errors = str(errors)
    f.user = ''

#pre_save.connect(run_csv_import, sender=CSVImport)
