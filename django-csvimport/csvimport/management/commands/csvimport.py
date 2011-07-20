# Run sql files via django#
# www.heliosfoundation.org
import sys, os, csv, re
from datetime import datetime
import codecs

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, BaseCommand
from optparse import make_option
from django.db import connection, transaction
from django.conf import settings
from django.db import models

from csvimport import models
# Note if mappings are manually specified they are of the following form ...
# MAPPINGS = "column1=shared_code,column2=org(Organisation|name),column3=description"
statements = re.compile(r";[ \t]*$", re.M)

def save_csvimport(props={}, instance=None):
    """ To avoid circular imports do saves here """
    if not instance:
        csvimport = models.CSVImport()
    for key in props.keys():
        csvimport.__setattr__(key, value)
    csvimport.save()
    return csvimport.id


class Command(LabelCommand):
    """
    Parse and map a CSV resource to a Django model.
    
    Notice that the doc tests are merely illustrational, and will not run 
    as is.
    """
    
    option_list = BaseCommand.option_list + (
               make_option('--mappings', default='', 
                           help='Please provide the file to import from'),
               make_option('--model', default='iisharing.Item', 
                           help='Please provide the model to import to'),
                   )
    help = "Imports a CSV file to a model"

    def handle_label(self, label, **options):
        """ Handle the circular reference by passing the nested
            save_csvimport function 
        """
        filename = label 
        mappings = options.get('mappings', []) #MAPPINGS)
        modelname = options.get('model', 'Item')
        show_traceback = options.get('traceback', True)
        self.setup(mappings, modelname, filename)
        self.props = {}
        errors = self.run()
        if self.props:
            save_csvimport(self.props)
        raise Exception(errors)
        return

    def setup(self, mappings, modelname, csvfile='', defaults=[],
              uploaded=None, nameindexes=False, deduplicate=True):
        """ Setup up the attributes for running the import """
        self.debug = False
        self.errors = []
        self.loglist = []
        self.defaults = defaults
        if modelname.find('.') > -1:
            app_label, model = modelname.split('.')
        self.app_label = app_label
        self.model = models.get_model(app_label, model)
        if mappings:
            self.mappings = self.__mappings(mappings)
        else:
            self.mappings = []
        self.nameindexes = bool(nameindexes) 
        self.file_name = csvfile
        self.deduplicate = deduplicate
        if uploaded:
            self.csvfile = self.__csvfile(uploaded.path)
        else:    
            self.check_filesystem(csvfile)

    def check_fkey(self, key, field):
        """ Build fkey mapping via introspection of models """
        #TODO fix to find related field name rather than assume second field
        if field.__class__ == models.ForeignKey:
            key += '(%s|%s)' % (field.related.parent_model.__name__,
                                field.related.parent_model._meta.fields[1].name,)
        return key

    def check_filesystem(self, csvfile):
        """ Check for files on the file system """
        if os.path.exists(csvfile):
            if os.path.isdir(csvfile):
                self.csvfile = []
                for afile in os.listdir(csvfile):
                    if afile.endswith('.csv'):
                        filepath = os.path.join(csvfile, afile)
                        try:
                            lines = self.__csvfile(filepath)
                            self.csvfile.extend(lines)
                        except:
                            pass
            else:
                self.csvfile = self.__csvfile(csvfile)
        if not getattr(self, 'csvfile', []):
            raise Exception('File %s not found' % csvfile)
    
    def run(self, logid=0):
        if self.nameindexes:
            indexes = self.csvfile.pop(0)
        counter = 0
        if logid:
            csvimportid = logid
        else:
            csvimportid = 0
        mapping = []
        if not self.mappings:
            fieldmap = {}
            for field in self.model._meta.fields:
                fieldmap[field.name] = field
            for i, heading in enumerate(self.csvfile[0]):
                for key in heading, heading.lower():
                    if fieldmap.has_key(key):
                        field = fieldmap[key]
                        key = self.check_fkey(key, field)
                        mapping.append('column%s=%s' % (i+1, key))
            mappingstr = ','.join(mapping)
            self.mappings = self.__mappings(mappingstr)            
        for row in self.csvfile[1:]:
            counter += 1
            model_instance = self.model()
            model_instance.csvimport_id = csvimportid
            for (column, field, foreignkey) in self.mappings:
                if self.nameindexes:
                    column = indexes.index(column)
                else:
                    column = int(column)-1

                row[column] = row[column].strip()
                
                if foreignkey:
                    row[column] = self.insert_fkey(foreignkey, row[column])

                if self.debug:
                    self.loglist.append('%s.%s = "%s"' % (self.model, field, row[column]))
                try:
                    model_instance.__setattr__(field, row[column])
                except:
                    try:
                        row[column] = model_instance.getattr(field).to_python(row[column])
                    except:
                        try:
                            row[column] = datetime(row[column])
                        except:
                            row[column] = None
                            self.loglist.append('Column %s failed' % field)
            if self.defaults:
                for (field, value, foreignkey) in self.defaults:
                    try:
                        done = model_instance.getattr(field)
                    except:
                        done = False
                    if not done:
                        if foreignkey:
                            value = self.insert_fkey(foreignkey, value)
                        model_instance.__setattr__(field, value)
            if self.deduplicate:
                matchdict = {}
                for (column, field, foreignkey) in self.mappings:
                    matchdict[field + '__exact'] = getattr(model_instance, 
                                                           field, None)
                try:
                    exists = self.model.objects.get(**matchdict)
                    continue
                except ObjectDoesNotExist:
                    pass
            try:
                model_instance.save()
            except Exception, err:
                self.loglist.append('Exception found... %s Instance %s not saved.' % (err, counter))
        if self.loglist:
            self.props = { 'file_name':self.file_name,
                           'import_user':'cron',
                           'upload_method':'cronjob',
                           'error_log':'\n'.join(self.loglist),
                           'import_date':datetime.now()}
            return self.loglist

    def insert_fkey(self, foreignkey, rowcol):
        """ Add fkey if not present 
            If there is corresponding data in the model already,
            we do not need to add more, since we are dealing with
            foreign keys, therefore foreign data
        """
        fk_key, fk_field = foreignkey
        if fk_key and fk_field:
            fk = models.get_model(self.app_label, fk_key)
            matches = fk.objects.filter(**{fk_field+'__exact': 
                                           rowcol})

            if not matches:
                key = fk()
                key.__setattr__(fk_field, rowcol)
                key.save()

            rowcol = fk.objects.filter(**{fk_field+'__exact': rowcol})[0]
        return rowcol
        
    def error(self, message, type=1):
        """
        Types:
            0. A fatal error. The most drastic one. Will quit the program.
            1. A notice. Some minor thing is in disorder.
        """
        
        types = (
            ('Fatal error', FatalError),
            ('Notice', None),
        )
        
        self.errors.append((message, type))
        
        if type == 0:
            # There is nothing to do. We have to quite at this point
            raise types[0][1], message
        elif self.debug == True:
            print "%s: %s" % (types[type][0], message)
    
    def __csvfile(self, datafile):
        #import chardet
        try:
            csvfile = codecs.open(datafile, 'r', 'utf-8')
        except IOError:
            self.error('Could not open specified csv file, %s, or it does not exist' % datafile, 0)
        else:
            # CSV Reader returns an iterable, but as we possibly need to
            # perform list commands and since list is an acceptable iterable, 
            # we'll just transform it.
            return list(self.unicode_csv_reader(csvfile))

    def unicode_csv_reader(self, unicode_csv_data, dialect=csv.excel, **kwargs):
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(self.utf_8_encoder(unicode_csv_data),
                                dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            yield [unicode(cell, 'utf-8') for cell in row]

    def utf_8_encoder(self, unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')
    
    def __model(self, model='Item'):
        # In order to properly import the models, and figure out what settings 
        # to use, we need to figure out the application and project names.
        try:
            from iisharing import models
        except ImportError:
            self.error('Specified directory does not exist')
        else:
            return models.Item
    
    def __mappings(self, mappings):
        """
        Parse the mappings, and return a list of them.
        """
        
        def parse_mapping(args):
            """
            Parse the custom mapping syntax (column1=field1(ForeignKey|field),
            etc.)
            
            >>> parse_mapping('a=b(c|d)')
            [('a', 'b', '(c|d)')]
            """
            
            pattern = re.compile(r'(\w+)=(\w+)(\(\w+\|\w+\))?')
            mappings = pattern.findall(args)
            
            mappings = list(mappings)
            for mapping in mappings:
                m = mappings.index(mapping)
                mappings[m] = list(mappings[m])
                mappings[m][2] = parse_foreignkey(mapping[2])
                mappings[m] = tuple(mappings[m])
            mappings = list(mappings)
            
            return mappings
            
        def parse_foreignkey(key):
            """
            Parse the foreignkey syntax (Key|field)
            
            >>> parse_foreignkey('(a|b)')
            ('a', 'b')
            """
            
            pattern = re.compile(r'(\w+)\|(\w+)', re.U)
            if key.startswith('(') and key.endswith(')'):
                key = key[1:-1]
                
            found = pattern.search(key)
            
            if found != None:
                return (found.group(1), found.group(2))
            else:
                return None
                    
        mappings = mappings.replace(',', ' ')
        mappings = mappings.replace('column', '')
        return parse_mapping(mappings)


class FatalError(Exception):
    """
    Something really bad happened.
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

