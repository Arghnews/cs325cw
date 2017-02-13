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

    operators = ['\+','-','\*','g','%','\^','#','==','~=',
            '<=','>=','<','>','=','\(','\)','\{','\}','\[',
            '\]',';',':',',','\.\.\.','\.\.','\.',]
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

# used in funcs when telling lookahead func
# what to look for, ie tuples of ",",MATCH_VALUE
MATCH_TYPE = "type"
MATCH_VALUE = "value"
MATCH_FUNCTION = "function_type"

firstSets = dict()

def parse(fname):

    firstSets["binop"] = [('+',MATCH_VALUE), ('-',MATCH_VALUE), ('*',MATCH_VALUE), ('/',MATCH_VALUE), ('^',MATCH_VALUE), ('%',MATCH_VALUE), '..', ('<',MATCH_VALUE), '<=', ('>',MATCH_VALUE), '>=', '==', '~=', 'and', 'or']
    firstSets["unop"] = [('-',MATCH_VALUE), ('not',MATCH_VALUE), ('#',MATCH_VALUE)]
    firstSets["fieldsep"] = [(',',MATCH_VALUE), (';',MATCH_VALUE)]
    firstSets["exp"] = [('nil',MATCH_VALUE),('false',MATCH_VALUE),('true',MATCH_VALUE),('Number', MATCH_TYPE), ('String', MATCH_TYPE), ('...', MATCH_VALUE),('function',MATCH_VALUE),('{',MATCH_VALUE),('Name',MATCH_TYPE),('-',MATCH_VALUE),('not',MATCH_VALUE),('#',MATCH_VALUE)]
    firstSets["args"] = [('(',MATCH_VALUE),('{',MATCH_VALUE),('String',MATCH_TYPE)]
    firstSets["tableconstructor"] = [('{',MATCH_VALUE)]
    firstSets["exp_back"] = [('[',MATCH_VALUE),('.',MATCH_VALUE)]
    firstSets["args_back"] = firstSets["args"] + [(':',MATCH_VALUE)]
    firstSets["exp_front"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]

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
    EOF = Token("EOF","EOF",0 if len(tokens) == 0 else tokens[-1].line+1,0)
    tokens.append(EOF)

    for i, t in enumerate(tokens):
        print(i,t)
    print("Now the program starts fo real")
    i = 0

    
    i_b = i
    i, tokens = laststat(i, tokens)
    print("laststat",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])
    return

    i_b = i
    i, tokens = prefixexp(i, tokens)
    print("prefixexp",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = varlist(i, tokens)
    print("varlist",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])
    i_b = i
    i, tokens = var(i, tokens)
    print("var",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = functioncall(i, tokens)
    print("functioncall",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = exp_args_back(i, tokens)
    print("exp_args_back",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = exp_front(i, tokens)
    print("exp_front",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = exp_back(i, tokens)
    print("exp_back",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = args_back(i, tokens)
    print("args_back",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = parlist(i, tokens)
    print("Consumed in parlist",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = parlist(i, tokens)
    print("Parlist 2",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = binop(i, tokens)
    print("Binop",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = unop(i, tokens)
    print("Unop",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = fieldsep(i, tokens)
    print("Fieldsep",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = funcname(i, tokens)
    print("funcname",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = field(i, tokens)
    print("field",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = fieldlist(i, tokens)
    print("fieldlist",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    i_b = i
    i, tokens = tableconstructor(i, tokens)
    print("tableconstructor",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

    #i_b = i
    #i, tokens = explist(i, tokens)
    #print("explist",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])

def laststat(i, tokens):
    if contains(i, tokens, [("return",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "return")
        i, tokens = optional(i, tokens, [(explist,MATCH_FUNCTION)], 1)
    elif contains(i, tokens, [("break",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "break")

    return i, tokens

def prefixexp(i, tokens):
    if contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
    elif contains(i, tokens, [("(",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "(")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, ")")
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
    return i, tokens

def varlist(i, tokens):
    i, tokens = var(i, tokens)
    i, tokens = star(i, tokens, [(",",MATCH_VALUE),(var,MATCH_FUNCTION)], 2)
    return i, tokens

def var(i, tokens):
    if contains(i, tokens, firstSets["exp_front"]):
        i, tokens = exp_front(i, tokens)
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
        i, tokens = exp_back(i, tokens)
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
    return i, tokens

def functioncall(i, tokens):
    i, tokens = exp_front(i, tokens)
    i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
    i, tokens = args_back(i, tokens)
    return i, tokens

def exp_args_back(i, tokens):
    if contains(i, tokens, firstSets["exp_back"]):
        i, tokens = exp_back(i, tokens)
    elif contains(i, tokens, firstSets["args_back"]):
        i, tokens = args_back(i, tokens)
    return i, tokens

def exp_front(i, tokens):
    if contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
    elif contains(i, tokens, [("(",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "(")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, ")")
    return i, tokens

def exp_back(i, tokens):
    if contains(i, tokens, [("[",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "[")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, "]")
    elif contains(i, tokens, [(".",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, ".")
        i, tokens = matchTypeNow(i, tokens, "Name")
    return i, tokens

def args_back(i, tokens):
    if contains(i, tokens, firstSets["args"]):
        i, tokens = args(i, tokens)
    elif contains(i, tokens, [(":",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, ":")
        i, tokens = matchTypeNow(i, tokens, "Name")
        i, tokens = args(i, tokens)
    return i, tokens

def args(i, tokens):
    if contains(i, tokens, [("(",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "(")
        i, tokens = optional(i, tokens, [(explist,MATCH_FUNCTION)], 1)
        i, tokens = matchValueNow(i, tokens, ")")
    elif contains(i, tokens, firstSets["tableconstructor"]):
        i, tokens = tableconstructor(i, tokens)
    elif contains(i, tokens, [("String",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "String")
    return i, tokens

def explist(i, tokens):
    i, tokens = star(i, tokens, [(exp,MATCH_FUNCTION),(",",MATCH_VALUE)], 2)
    i, tokens = exp(i, tokens)
    return i, tokens

def tableconstructor(i, tokens):
    i, tokens = matchValueNow(i, tokens, "{")
    i, tokens = optional(i, tokens, [(fieldlist,MATCH_FUNCTION)], 1)
    i, tokens = matchValueNow(i, tokens, "}")
    return i, tokens

def fieldlist(i, tokens):
    i, tokens = field(i, tokens)
    i, tokens = star(i, tokens, [(fieldsep,MATCH_FUNCTION),(field,MATCH_FUNCTION)], 2)
    i, tokens = optional(i, tokens, [(fieldsep,MATCH_FUNCTION)], 1)
    return i, tokens

def field(i, tokens):
    if contains(i, tokens, [("[",MATCH_VALUE)]):
        # todo, fill the aftermath of each of these
        # with checks and should haves
        i, tokens = matchValueNow(i, tokens, "[")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, "]")
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
    elif contains(i, tokens, firstSets["exp"]):
        i, tokens = exp(i, tokens)
    return i, tokens
    
def exp(i, tokens):
    return matchTypeNow(i,tokens,"String")
    #return i, tokens

def funcname(i, tokens):
    i, tokens = matchTypeNow(i,tokens,"Name")
    i, tokens = star(i, tokens, [(".",MATCH_VALUE), ("Name",MATCH_TYPE)], 2)
    i, tokens = optional(i, tokens, [(":",MATCH_VALUE), ("Name",MATCH_TYPE)], 2)
    return i, tokens

def parlist(i, tokens):
    # chosen the ... only
    if contains(i, tokens, [("...",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "...")
    # namelist
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = namelist(i, tokens)
        i, tokens = optional(i, tokens, [(",",MATCH_VALUE),("...",MATCH_VALUE)], 2)
    else:
        print("This is not the parlist you've been looking for")
    
    return i, tokens

def namelist(i, tokens):
    i, tokens = matchTypeNow(i,tokens,"Name")
    i, tokens = star(i, tokens, [(",",MATCH_VALUE), ("Name",MATCH_TYPE)], 2)
    return i, tokens

def binop(i, tokens):
    return matchTerminalInList(i, tokens, firstSets["binop"])

def unop(i, tokens):
    unop_list = ['-', 'not', '#']
    return matchTerminalInList(i, tokens, firstSets["unop"])

def fieldsep(i, tokens):
    fieldsep_list = [',', ';']
    return matchTerminalInList(i, tokens, firstSets["fieldsep"])









def contains(i, tokens, firstSet):
    for _, (val,match_type) in enumerate(firstSet):
        b = False
        if match_type == MATCH_VALUE:
            b = match_v(tokens, i, val)
        elif match_type == MATCH_TYPE:
            b = match_t(tokens, i, val)
        if b:
            return True
    return False

def matchTerminalListError(i, tokens, list, err):
    i_b = i
    i, tokens = matchTerminalInList(i, tokens, list)
    #if i == i_b:
        #print(err)
    return i, tokens

def matchTerminalInList(i, tokens, list):
    for op in list:
        if lookahead(i, tokens, [op], 1):
            i, tokens = matchValueNow(i, tokens, op[0])
            break
    return i, tokens

def matchTypeNow(i, tokens, type):
    return matchType(type)(i,tokens)

def matchValueNow(i, tokens, value):
    return matchValue(value)(i,tokens)

def matchType(type):
    def f(i, tokens):
        if match_t(tokens,i,type):
            i += 1
        return i, tokens
    # for nice error print
    f.__name__ = type
    return f

def matchValue(value):
    def f(i, tokens):
        if match_v(tokens,i,value):
            i += 1
        return i, tokens
    # for nice error print
    f.__name__ = value
    return f

# lookahead function right here
def lookahead(i, tokens, func_tuples, lookahead_n):
    for j in range(0, min(len(func_tuples),lookahead_n)):
        b = False
        if func_tuples[j][1] == MATCH_VALUE:
            b = match_v(tokens, i+j, func_tuples[j][0])
        elif func_tuples[j][1] == MATCH_TYPE:
            b = match_t(tokens, i+j, func_tuples[j][0])
        elif func_tuples[j][1] == MATCH_FUNCTION:
            b = i_changed(i+j, tokens, func_tuples[j][0])
        if not b:
            return False
    return True

def i_changed(i, tokens, f):
    i_b = i
    i_after, _ = f(i, tokens)
    return i_b != i_after

def star_do(i, tokens, funcs):
    while True:
        for f in funcs:
            i, tokens = f(i, tokens)
        yield i, tokens

def optional_do(i, tokens, funcs):
    for f in funcs:
        i, tokens = f(i, tokens)
    yield i, tokens

def something(i, tokens, func_tuples, lookahead_n, repeater):
    # creates list of funcs that are that grammar
    # thing that we're doing
    funcs = []
    for _, (match, match_type) in enumerate(func_tuples):
        if match_type == MATCH_VALUE:
            funcs.append(matchValue(match))
        elif match_type == MATCH_TYPE:
            funcs.append(matchType(match))
        elif match_type == MATCH_FUNCTION:
            funcs.append(match)

    if lookahead(i, tokens, func_tuples, lookahead_n):
        for i, tokens in repeater(i, tokens, funcs):
            if not lookahead(i, tokens, func_tuples, lookahead_n):
                break

    return i, tokens

def optional(i, tokens, func_tuples, lookahead):
    return something(i, tokens, func_tuples, lookahead, optional_do)

def star(i, tokens, func_tuples, lookahead):
    return something(i, tokens, func_tuples, lookahead, star_do)

def match_t(tokens,i,type):
    return i < len(tokens) and tokens[i].type == type

def match_v(tokens,i,val):
    return i < len(tokens) and tokens[i].value == val

if __name__ == "__main__":
    parse(sys.argv[1])
