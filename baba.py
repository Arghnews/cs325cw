#!/usr/bin/env python3

import collections
import re
import copy
import sys

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
            elif kind == "Name" and value in keywords:
                kind = "Keyword" # to convert keywords picked up as names to keywords
            column = mo.start() - line_start
            yield Token(kind, value, line_num, column)

blablablabla='''
x = 0x3p3
print(x)

a = 10
b = 30

function max(num1, num2)

   if (num1 > num2) then
      result = num1;
   else
      result = num2;
   end

   return result; 
end

while( false )
do
   print("This loop will run forever.")
end
'''

btick = r'`'
ftick = r'´'

def parse(fname):
    # ^([0-9]*)(\.[0-9]+)?([eE]-?[0-9]+)?$|^([0-9]+)(\.[0-9]*)?([eE]-?[0-9]+)?$|^0x([0-9a-fA-F]*)(\.[0-9a-fA-F]+)?([pP]-?[0-9]+)?$|^0x([0-9a-fA-F]+)(\.[0-9a-fA-F]*)?([pP]-?[0-9]+)?$
    program = ""
    with open(fname, "r") as ins:
        for line in ins:
            program += line


#function max(num1, num2)
    tokens = []
    for token in tokenize(program):
        tokens.append(token)
    # append EOF token
    EOF = Token("EOF","EOF",tokens[-1].line+1,0)
    tokens.append(EOF)

    for i, t in enumerate(tokens):
        print(i,t)
    print("Now the program starts fo real")

    i = 0
    i_b = i
    i, tokens = namelist(i, tokens)
    print("Consumed in namelist",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])
    #i_b = i
    #i, tokens = namelist(i, tokens)
    #print("Consumed in namelist",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

def matchType(type):
    def f(i, tokens):
        if match_t(tokens[i],type):
            i += 1
        return i, tokens
    # for nice error print
    f.__name__ = type
    return f

def matchValue(value):
    def f(i, tokens):
        if match_v(tokens[i],value):
            i += 1
        return i, tokens
    # for nice error print
    f.__name__ = value
    return f

def name_suffix(i, tokens):
    if match_v(tokens[i],","):
        i += 1
        i, tokens = name(i, tokens)
    else:
        pass
    return i, tokens

def star(i, tokens, funcs):
    cont = True
    while cont:
        original_i = i
        for f in funcs:
            last_i = i
            i, tokens = f(i, tokens)
            cont = last_i != i
            if i == original_i:
                # fine, not another instance of a in
                # a*
                print("Fine return",tokens[i])
                return original_i, tokens
            elif not cont:
                # error, as for a -> b { c d}
                # got b c q as d != q
                print("Error, expected ",f.__name__)
                return original_i, tokens
    return i, tokens

def optional(i, tokens, funcs):
    cont = True
    original_i = i
    for f in funcs:
        last_i = i
        i, tokens = f(i, tokens)
        cont = last_i != i
        if i == original_i:
            # fine, not another instance of a in
            # a*
            print("Fine return",tokens[i])
            return original_i, tokens
        elif not cont:
            # error, as for a -> b { c d}
            # got b c q as d != q
            print("Error, expected ",f.__name__)
            return original_i, tokens
    return i, tokens

def namelist(i, tokens):
    i, tokens = matchType("Name")(i,tokens)
    i, tokens = optional(i, tokens, [matchValue(","),matchType("Name")])
    return i, tokens

def match_t(token,type):
    return token.type == type

def match_v(token, val):
    return token.value == val

if __name__ == "__main__":
    parse(sys.argv[1])
