from django.db import models

CHOICES = (('manual','manual'),('cronjob','cronjob'))
# Create your models here.

class CSVImport(models.Model):
    """ Logging model for importing files """
    model_name = models.CharField(max_length=255, blank=True, 
                                  default='iisharing.Item',
                        help_text='Please specify the app_label.model_name')
    field_list = models.CharField(max_length=255, blank=True,
                        help_text='''Enter list of fields in order, 
                                     or use CSV with all fields in order, 
                                     or a header row with field names''')
    upload_file = models.FileField(upload_to='tmp')
    file_name = models.CharField(max_length=255, blank=True)
    encoding = models.CharField(max_length=32, blank=True)
    upload_method = models.CharField(blank=False, max_length=50, 
                                     default='manual', choices=CHOICES)    
    error_log = models.TextField(help_text='Each line is an import error')
    import_date = models.DateField(auto_now=True)
    import_user = models.CharField(max_length=255, default='anonymous',
                                   help_text='User id as text', blank=True)

    def __unicode__(self):
        return self.upload_file.name

