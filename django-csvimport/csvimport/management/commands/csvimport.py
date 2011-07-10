# Run sql files via django#
# www.heliosfoundation.org
import sys, os, csv, re

from django.core.management.base import LabelCommand, BaseCommand
from optparse import make_option
from django.db import connection, transaction
from django.conf import settings
from django.db import models
# TODO : just use a field name list and find fkeys from model 
# + default try fields in the order they are in the model and no MAPPINGS at all
MAPPINGS = "column1=shared_code,column2=org_code,column3=organization(Organization|name),column4=description,column5=unit_of_measure(UnitOfMeasure|name),column6=quantity,column7=status"
statements = re.compile(r";[ \t]*$", re.M)

class Command(LabelCommand):
    """
    Parse and map a CSV resource to a Django model.
    
    Notice that the doc tests are merely illustrational, and will not run 
    as is.
    """
    
    option_list = BaseCommand.option_list + (
               make_option('--mappings', default=MAPPINGS, 
                           help='Please provide the file to import from'),
               make_option('--model', default='iisharing.Item', 
                           help='Please provide the model to import to'),
                   )
    help = "Imports a CSV file to a model"

    def handle_label(self, label, **options):
        filename = label 
        mappings = options.get('mappings', MAPPINGS)
        modelname = options.get('model', 'Item')
        if modelname.find('.') > -1:
            app_label, modelname = modelname.split('.')
        show_traceback = options.get('traceback', True)
        self.setup(filename, mappings, modelname, app_label)
        self.run()
        return

    def setup(self, csvfile, mappings, model, 
              app_label='iisharing', nameindexes=False):
        # This setting can be overriden at any time through an 
        # instance.debug = True, but this is for the hardcore crowd, and
        # should not polute the API
        self.debug = False
        self.errors = []
        self.loglist = []
        self.app_label = app_label
        self.model = models.get_model(app_label, model)
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
        self.mappings = self.__mappings(mappings)
#        raise Exception(self.model)
        self.nameindexes = bool(nameindexes)
    
    def run(self):
        if self.nameindexes:
            indexes = self.csvfile.pop(0)
        counter = 0
        for row in self.csvfile:
            counter += 1
            model_instance = self.model()
            for (column, field, foreignkey) in self.mappings:
                if self.nameindexes:
                    column = indexes.index(column)
                else:
                    column = int(column)-1
                    
                row[column] = row[column].strip()
                
                if foreignkey:
                    fk_key, fk_field = foreignkey
                    fk = models.get_model(self.app_label, fk_key)
                    # If there is corresponding data in the model already,
                    # we do not need to add more, since we are dealing with
                    # foreign keys, therefore foreign data
                    matches = fk.objects.filter(**{fk_field+'__exact': 
                                                   row[column]})
                    
                    if not matches:
                        key = fk()
                        key.__setattr__(fk_field, row[column])
                        key.save()

                    row[column] = fk.objects.filter(**{fk_field+'__exact': row[column]})[0]
                if self.debug:
                    self.loglist.append('%s.%s = "%s"' % (self.model, field, row[column]))

                try:
                    model_instance.__setattr__(field, row[column])
                except:
                    try:
                        row[column] = model_instance.getattr(field).to_python(row[column])
                    except:
                        self.loglist.append('Column %s failed' % field)
            try:
                model_instance.save()
            except Exception, err:
                self.loglist.append('Exception found... %s Instance %s not saved.' % (err, counter))
        if self.loglist:
            raise Exception(self.loglist)

        
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
        try:
            csvfile = file(datafile, 'rU')
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

