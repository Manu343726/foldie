
import re

class DataTranslator(object):


    def __init__(self, holders):
        self.holders = holders

        self.patterns = {
            'variable': re.compile('\$\((?P<index>.*?)\)')
            # 'datatype_apply': re.compile('\$\{(?P<datatype>.*?)\}\((?P<args>.*?)\)')
            # 'data_property': re.compile('\$\[(?P<property>.*?)\]')
        }

    def _parse_args(self, data, args):
        specialization = '_parse_args_{}'.format(type(data).__name__)

        if hasattr(self, specialization):
            return getattr(self, specialization)(data, args)

        if '...' in args:
            return self._parse_args_variadic(data,args)
        else:
            try:
                return self.translate(data[int(args) - 1])
            except TypeError:
                return str(data)

    def _parse_args_variadic(self, data,args):

        if len(data) > 1:
            begin, end = args.split('...')

            begin = int(begin) if begin else 1
            end = int(end) if end else len(data)

            print 'args: "{}". begin={}, end={}'.format(args, begin, end)

            return ','.join([self.translate(data[i]) for i in xrange(begin-1, end)])
        else:
            return str(data)

    def _process_pattern(self, data, pattern, input):
        def replace(match):
            print 'GROUP: "{}"'.format(match.groups(0)[0])
            return self._parse_args(data, match.groups(0)[0])

        return pattern.sub(replace, input)

    def _parse_variables(self, data, pattern, input):
        def replace(match):
            print 'DATA: "{}"'.format(data)
            print 'INPUT: "{}"'.format(input)
            print 'GROUP: "{}"'.format(match.groups(0)[0])
            return self._parse_args(data, match.groups(0)[0])

        return pattern.sub(replace, input)

    def translate(self, data):
        holder = self.holders[type(data).__name__]

        translation = holder

        for category, pattern in self.patterns.items():
            translation = getattr(self, '_parse_{}s'.format(category))(data, pattern, translation)

        return translation

    def __call__(self, data):
        return self.translate(data)



