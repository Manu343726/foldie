
from holderparsing import DataTranslator
from yaml import load
import sys
import ast


class FoldieCompiler(object):

    FOLDIE_NAMESPACE = 'foldie'
    FOLDIE_INPUT_NAMESPACE = 'input'


    def __init__(self, settings):
        self.settings = settings
        self.translator = DataTranslator(self.settings['datatypes'])

    @staticmethod
    def from_file(foldie_file):
        return FoldieCompiler(load(open(foldie_file, 'r').read()))

    @staticmethod
    def from_settings(settings):
        return FoldieCompiler(settings)


    def foldie_main(self):
        main_header = 'int main(){'

        for output_var in self.settings['output'].items():
            main_header += '    std::cout << {}<{}>() << std::endl;\n'.format(self.settings['to_runtime'],
                                   output_var)

        return main_header + '}'

    def foldie_variables(self):
        def mapping(x):
            try:
                return '    using {} = {};'.format(x[0], self.translator(ast.literal_eval(str(x[1]))))
            except Exception as e:
                print '"{}" x={}'.format(e, x[1])
                raise e

        return '\n'.join(map(mapping, self.settings['input'].items()))

    def foldie_warnings(self):
        if self.settings['settings']['verbose'] > 0:
            def mapping(x):
                return '    #warning "FOLDIE INPUT VARIABLE: {} = {}"'.format(x[0], x[1])

            return '\n'.join(map(mapping, self.settings['input'].items())) + '\n'
        else:
            return ''


    def foldie_hpp(self):
        header = \
"""
#ifndef FOLDIE_HEADER_HPP
#define FOLDIE_HEADER_HPP

namespace {0} {{ namespace {1} {{
{2}
{3}
}} }}

#endif /* FOLDIE_HEADER_HPP */
"""

        return header.format(self.FOLDIE_NAMESPACE,
                       self.FOLDIE_INPUT_NAMESPACE,
                       self.foldie_warnings(),
                       self.foldie_variables())

    def foldie_cmake_args(self):
        return '-DFOLDIE=TRUE -DCMAKE_VERBOSE_MAKEFILE={} \
                -DFOLDIE_MAIN=\"{}\"'.format('ON' if self.settings['settings']['verbose'] >= 2 else 'OFF',
                       self.foldie_main())



def main():
    compiler = FoldieCompiler.from_file(sys.argv[1])

    with file(compiler.settings['header'], 'w') as header:
        header.write(compiler.foldie_hpp())


if __name__ == "__main__":
    main()
