#!/usr/bin/env python3

import collections
import re

Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

def tokenize(code):
    keywords = ["and","break","do","else","elseif","end","false",
            "for","function","if","in","local","nil","not","or",
            "repeat","return","then","true","until","while"]
    keywords_regex = (r'|').join(word for word in keywords)

    operators = ['\+','\-','\*','\/','\%','\^','\#','\==','\~=',
            '\<=','\>=','\<','\>','\=','\(','\)','\{','\}','\[',
            '\]','\;','\:','\,','\...','\..','\.',]
    operators_regex = (r'|').join(word for word in operators)
    
    #inty = r'asd'
    #int2 = r'asdd'
    #int3 = r'|'.join([inty, int2])
    token_specification = [
        # Order in the Number matters, hex first
        ("Number", r'0[xX]([0-9a-fA-F]*)(\.[0-9a-fA-F]+)([pP]-?[0-9]+)?|0[xX]([0-9a-fA-F]+)(\.[0-9a-fA-F]*)?([pP]-?[0-9]+)?|([0-9]+)(\.[0-9]*)?([eE]-?[0-9]+)?|([0-9]*)(\.[0-9]+)([eE]-?[0-9]+)?' ),
        ("Name", r'[_a-zA-Z][_a-zA-Z0-9]*'), # should be before keyword
        ("Keyword", keywords_regex),
        ("Operator", operators_regex),
        ("String", r'\"[^\"]*\"|\'[^\']*\''),
        ("Newline", r'\n'),
        ("Empty", r' '),
        ("Error", r'.'), # Must be last
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == "Newline":
            line_start = mo.end()
            line_num += 1
        elif kind == "Empty":
            pass
        elif kind == 'Error':
            raise RuntimeError('%r unexpected on line %d' % (value, line_num))
        else:
            if kind == "String" and value:
                value = value[1:-1] # remove first and last chars
            column = mo.start() - line_start
            yield Token(kind, value, line_num, column)

def main():
    statements = '''
    a = "a"
    b = '"66"'
    if{}{
    iffy
        35.53e-53
        xx
        0x3aA.Ap-3
        e
    '''
    # ^([0-9]*)(\.[0-9]+)?([eE]-?[0-9]+)?$|^([0-9]+)(\.[0-9]*)?([eE]-?[0-9]+)?$|^0x([0-9a-fA-F]*)(\.[0-9a-fA-F]+)?([pP]-?[0-9]+)?$|^0x([0-9a-fA-F]+)(\.[0-9a-fA-F]*)?([pP]-?[0-9]+)?$

    for token in tokenize(statements):
        print(token)

if __name__ == "__main__":
    main()
