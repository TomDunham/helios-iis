# Run sql files via django
import sys, os, csv, re

from django.core.management.base import BaseCommand, AppCommand
from optparse import make_option
from django.db import connection, transaction
from django.conf import settings

statements = re.compile(r";[ \t]*$", re.M)

class CSVImport(AppCommand):
    """
    Parse and map a CSV resource to a Django model.
    
    Notice that the doc tests are merely illustrational, and will not run 
    as is.
    """
    
    option_list = BaseCommand.option_list + (
               make_option('--file', default='import.csv', model='Item',
                           help='Please provide the file and model to import to'),
                   )
    help = "Imports a CSV file to a model"

    def handle_app(self, app, **options):
        filename = options.get('file', 'import.csv')
        modelname = options.get('model', 'Item')
        verbosity = options.get('verbosity', 1)        
        show_traceback = options.get('traceback', True)

        app_dir = os.path.normpath(os.path.join(os.path.dirname(app.__file__), 'fixtures'))
        return

    def setup(self, csvfile, mappings, model, modelspy, nameindexes=False):
        # This setting can be overriden at any time through an 
        # instance.debug = True, but this is for the hardcore crowd, and
        # should not polute the API
        self.debug = False
        self.errors = []

        self.csvfile = self.__csvfile(csvfile)
        self.mappings = self.__mappings(mappings)
        self.modelspy = self.__modelspy(modelspy)
        self.model = model #self.__model(model)
#        raise Exception(self.model)
        self.nameindexes = bool(nameindexes)
    
    def run(self):
        if self.nameindexes:
            indexes = self.csvfile.pop(0)
            
        for row in self.csvfile:
            model_instance = getattr(self.models, self.model)()
            
            for (column, field, foreignkey) in self.mappings:
                if self.nameindexes:
                    column = indexes.index(column)
                else:
                    column = int(column)-1
                    
                row[column] = row[column].strip()
                
                if foreignkey:
                    fk_key, fk_field = foreignkey
                    try:
                        fk = getattr(self.models, fk_key)
                    except AttributeError:
                        self.error('Referenced foreign keys must be in specified models.py', 0)
                
                    # If there is corresponding data in the model already,
                    # we do not need to add more, since we are dealing with
                    # foreign keys, therefore foreign data
                    matches = fk.objects.filter(**{fk_field+'__exact': 
                    row[column]})
                    
                    if not matches:
                        key = fk()
                        key.__setattr__(fk_field, row[column])
                        key.save()
                    
                    row[column] = fk.objects.filter(**{fk_field+'__exact': 
                    row[column]})[0]
            
                print '%s.%s = "%s"' % (self.model, field, row[column])
                model_instance.__setattr__(field, row[column])

            try:
                model_instance.save()
            except:
                print 'Exception found... Instance not saved.'

            print '-' * 20
        
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
            csvfile = file(datafile, 'r')
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

    def __modelspy(self, modelspy):
        # We need the path containing the models.py, so if it's in the
        # specified path, we'll just remove it.
        if modelspy.endswith('models.py'):
            self.error('Specified models.py path has "models.py" in it.', 1)
            modelspy = modelspy[:-9]

        if not os.path.exists(modelspy):
            self.error('Specified directory does not contain a models.py', 0)

        return modelspy
    
    def __model(self, model):
        # In order to properly import the models, and figure out what settings 
        # to use, we need to figure out the application and project names.
        a_dir = os.path.abspath(self.modelspy)
        a_name = os.path.basename(a_dir)
        p_dir = os.path.dirname(a_dir)
        p_name = os.path.basename(p_dir)
        
        # To import the models.py, it needs to be in sys.path
        sys.path.append(os.path.abspath(self.modelspy))
        # The project path should too
        sys.path.append(os.path.dirname(p_dir))
        
        os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % p_name
        
        try:
            self.models = __import__('%s.%s.models' % (p_name, a_name),
            globals(), locals(), '%s.%s' % (p_name, p_name))
        except ImportError:
            self.error('Specified directory does not exist')
        else:
            return model
    
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
        return parse_mapping(mappings)

class FatalError(Exception):
    """
    Something really bad happened.
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage='csvimport.py [args]', version='CSV Import %s' % __version__)
    
    try:
        sys.argv[1]
    except IndexError:
        parser.error('No arguments specified')
        
    parser.add_option('-n', '--name-indexes',
    action='store_true', dest='nameindexes',
    help='If this flag is on, the first line of the CSV file will be used as an index reference, meaning the mapping will appear as columnname=modelname. If it is not on, columns should instead be referred to by their position (first column is 1, second is 2, etc.)')
    
    parser.add_option('-c', '--csv',
    action='store', type='string', dest='csvfile',
    help='The desired CSV file to import from')
    
    parser.add_option('-p', '--modelspy',
    action='store', type='string', dest='modelspy',
    help='The mapping, to specify which columns from the CSV file that go with which models.')
    
    parser.add_option('-m', '--model',
    action='store', type='string', dest='model',
    help='The model to perform the mapping on. Must be in the specified models.py')
    
    parser.add_option('-a', '--mappings',
    action='store', type='string', dest='mappings',
    help='The mapping, to specify which columns from the CSV file that go with which models. Written as a list of column=field, eg. column1=field1,column2=field2. No spaces. Foreign keys are specified by appending (key|field), where key is the name of the foreign key, and field is the attribute in the foreign key, that holds the data specified in the CSV column.')
    
    opts, args = parser.parse_args()
    
    if not opts.csvfile or not opts.modelspy or not opts.model or not\
    opts.mappings:
        parser.error('Not enough arguments specified.')
    
    try:
        c = CSVImport(opts.csvfile, opts.mappings, opts.model, opts.modelspy,
                      opts.nameindexes)
        c.run()
    except FatalError, e:
        parser.error(e)
