
from pyparsing import Word, Group, Literal, Keyword, nums, Or

FOLDIE_HOLDER_VARIABLE_TAG = '@'


class ParsingException(Exception):
    pass


class TagParser(object):

    def __call__(self, str):
        return self.parse(str)


class ValueTagParser(TagParser):
    '''
    Parses tags representing values.
    Those tags are usually indexed
    '''

    def __init__(self):
        self.tag = Literal(FOLDIE_HOLDER_VARIABLE_TAG)

        def idx(x):
            return int(x[0]) - 1

        self.value = Group(self.tag + Word(nums).setParseAction(idx)('idx'))

    def parse(self, str):
        matches = {}

        for tokens, prev, next in self.value.scanString(str):
            for _, idx in tokens:
                if  idx in matches:
                    raise ParsingException('Variable "{}{}" appears \
                                            multiple times in "{}"'
                                            .format(FOLDIE_HOLDER_VARIABLE_TAG,
                                                    tokens['idx'],
                                                    str))
                matches[idx] = prev + 1, next - 1
            

        return matches


class VariadicTagParser(TagParser):
    '''
    Parses tags representing variadic packs.
    '''

    def __init__(self):
        self.varadico = Keyword(FOLDIE_HOLDER_VARIABLE_TAG + '...')('varadico')

    def parse(self, str):
        matches = [(prev+1, next-1) for _, prev, next in self.varadico.scanString(str)]

        if len(matches) > 1:
            raise ParsingException('Variable "{}..." appears \
                                    multiple times in "{}"'
                                    .format(FOLDIE_HOLDER_VARIABLE_TAG,
                                            str))

        return matches


def replace_string_range(source, begin, end, replace):
    left = source[:begin-1]
    right = source[end+1:]

    return left + replace + right
        

class DataTranslator(object):

    DEFAULT_HOLDERS = {
        "int":  "tml::integral_constant<int,@1>",
        "list": "tml::list<@...>",
        "pair": "tml::maps::pair<@1,@2>",
        "dict": "tml::maps::map<@...>"
    }


    def __init__(self, holders=DEFAULT_HOLDERS):
        self.holders = holders
        self._parsed_holders = {}
        self._parse_holders()

    def _parse_holders(self):
        value_parser = ValueTagParser()
        variadic_parser = VariadicTagParser()
        

        def run_parsers():
            try:
                variadic = variadic_parser(holder)
                value = value_parser(holder)

                if len(variadic) > 0:
                    return variadic

                if len(value) > 0:
                    return value

            except ParsingException:
                return variadic

        for category, holder in self.holders.items():
            self._parsed_holders[category] = run_parsers()
            

    def translate(self, data):
        return getattr(self, '_translate_{}'.format(type(data).__name__))(data)

    def __call__(self, data):
        return self.translate(data)

    def _translate_int(self, data):
        holder = self.holders['int']

        begin, end = self._parsed_holders['int'][0]

        return replace_string_range(holder, begin, end, str(data))

    def _translate_pair(self, data):
        holder = self.holders['pair']

        for i in range(0,2):
            holder = holder.replace('{}{}'.format(FOLDIE_HOLDER_VARIABLE_TAG, i+1), self.translate(data[i]))

        return holder

    def _translate_list(self, data):
        holder = self.holders['list']

        return holder.replace('{}...'.format(FOLDIE_HOLDER_VARIABLE_TAG), ','.join(map(self.translate, data)))

    def _translate_tuple(self, data):
        if len(data) == 2: 
            return self._translate_pair(data)
        else:
            return self._translate_list(data)


