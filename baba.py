#!/usr/bin/env python3

import collections
import re
import copy
import sys
import traceback

Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

def tokenize(code):
    code = code.replace("\t"," ")
    code = code.replace("  "," ")
    keywords = ["and","break","do","else","elseif","end","false",
            "for","function","if","in","local","nil","not","or",
            "repeat","return","then","true","until","while"]
    keywords_regex = (r'|').join(word for word in keywords)

    operators = ['\+','-','\*','/','%','\^','#','==','~=',
            '<=','>=','<','>','=','\(','\)','\{','\}','\[',
            '\]',';',':',',','\.\.\.','\.\.','\.',]
    operators_regex = (r'|').join(op for op in operators)

    token_specification = [
            # Order in the Number matters, hex first
            ("Comment", r'--.*\n'), # only works on single line comment
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

    line_number = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == "Newline":
            line_start = mo.end()
            line_number += 1
        elif kind == "Empty" or kind == "Comment":
            pass
        elif kind == 'Error':
            raise RuntimeError('%r unexpected on line %d' % (value, line_number))
        else:
            if kind == "String" and value:
                value = value[1:-1] # remove first and last chars
            elif kind == "Name" and value in keywords:
                kind = "Keyword" # to convert keywords picked up as names to keywords
            column = mo.start() - line_start
            yield Token(kind, value, line_number, column)

# used in funcs when telling lookahead func
# what to look for, ie tuples of ",",MATCH_VALUE
MATCH_TYPE = "type"
MATCH_VALUE = "value"
MATCH_FUNCTION = "function_type"

firstSets = dict()

errors_switch = 0

varnames = []
# list of tuples that are to id this case
# of function names for lambdas
    #a, b = function(argy1) end, function(argy2) end
    #[(a_start, a_end), (b_start, b_end)]

expnames = []
# same as above for expressions

recent_parameter_list = []
# stack of tuples that are the args

def error(*err):
    global errors_switch
    if errors_switch == 0:
        print(err)

# why predictive parsing, faster

def parse(fname):

    firstSets["binop"] = [('+',MATCH_VALUE), ('-',MATCH_VALUE), ('*',MATCH_VALUE), ('/',MATCH_VALUE), ('^',MATCH_VALUE), ('%',MATCH_VALUE), ('..',MATCH_VALUE), ('<',MATCH_VALUE), ('<=',MATCH_VALUE), ('>',MATCH_VALUE), ('>=',MATCH_VALUE), ('==',MATCH_VALUE), ('~=',MATCH_VALUE), ('and',MATCH_VALUE), ('or',MATCH_VALUE)]
    firstSets["exp"] = [('nil',MATCH_VALUE),('false',MATCH_VALUE),('true',MATCH_VALUE),('Number', MATCH_TYPE), ('String', MATCH_TYPE), ('...', MATCH_VALUE),('function',MATCH_VALUE),('{',MATCH_VALUE),('Name',MATCH_TYPE),('-',MATCH_VALUE),('not',MATCH_VALUE),('#',MATCH_VALUE)]
    firstSets["stat_local"] = [('Name',MATCH_TYPE),('function',MATCH_VALUE)]
    firstSets["stat_for"] = [('Name',MATCH_TYPE)]
    firstSets["functiondef"] = [('function',MATCH_VALUE)]
    firstSets["funcbody"] = [('(',MATCH_VALUE)]
    firstSets["laststat"] = [('return',MATCH_VALUE),('break',MATCH_VALUE)]
    firstSets["prefixexp"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]
    firstSets["varlist"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]
    firstSets["exp_front"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]
    firstSets["var"] = [('Name',MATCH_TYPE)] + firstSets["exp_front"]
    firstSets["functioncall"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]
    firstSets["stat"] = firstSets["varlist"] + firstSets["functioncall"] + [('do',MATCH_VALUE), ('while',MATCH_VALUE), ('repeat',MATCH_VALUE), ('if',MATCH_VALUE), ('for',MATCH_VALUE), ('function',MATCH_VALUE), ('local',MATCH_VALUE)]
    firstSets["chunk"] = firstSets["stat"] + firstSets["laststat"] + [('EOF',MATCH_TYPE)]
    firstSets["block"] = firstSets["chunk"]
    firstSets["args"] = [('(',MATCH_VALUE),('{',MATCH_VALUE),('String',MATCH_TYPE)]
    firstSets["exp_back"] = [('[',MATCH_VALUE),('.',MATCH_VALUE)]
    firstSets["args_back"] = firstSets["args"] + [(':',MATCH_VALUE)]
    firstSets["exp_args_back"] = firstSets["exp_back"] + firstSets["args_back"]
    firstSets["explist"] = firstSets["exp"]
    firstSets["tableconstructor"] = [('{',MATCH_VALUE)]
    firstSets["fieldlist"] = [('[',MATCH_VALUE),('Name',MATCH_TYPE)] + firstSets["exp"]
    firstSets["field"] = [('[',MATCH_VALUE),('Name',MATCH_TYPE)] + firstSets["exp"]
    firstSets["funcname"] = [('Name',MATCH_TYPE)]
    firstSets["namelist"] = [('Name',MATCH_TYPE)]
    firstSets["parlist"] = [('Name',MATCH_TYPE), ('...',MATCH_VALUE)]
    firstSets["fieldsep"] = [(',',MATCH_VALUE), (';',MATCH_VALUE)]
    firstSets["unop"] = [('-',MATCH_VALUE), ('not',MATCH_VALUE), ('#',MATCH_VALUE)]
    firstSets["exp_p"] = firstSets["namelist"] +firstSets["fieldsep"] + firstSets["laststat"] + firstSets["binop"] + [('do',MATCH_VALUE),('then',MATCH_VALUE),(',',MATCH_VALUE),(')',MATCH_VALUE),(']',MATCH_VALUE),(';',MATCH_VALUE),("EOF",MATCH_TYPE),('until',MATCH_VALUE),('end',MATCH_VALUE),('else',MATCH_VALUE),('elseif',MATCH_VALUE),('}',MATCH_VALUE),('function',MATCH_VALUE) ]

    ## add followset of stat to exp_p
    ## add followset of chunk to exp_p
    ## add followset of field to exp_p
    ## add followset of explist to exp_p
    ## add followset of stat_local to exp_p
    ## add followset of laststat to exp_p

    # ^([0-9]*)(\.[0-9]+)?([eE]-?[0-9]+)?$|^([0-9]+)(\.[0-9]*)?([eE]-?[0-9]+)?$|^0x([0-9a-fA-F]*)(\.[0-9a-fA-F]+)?([pP]-?[0-9]+)?$|^0x([0-9a-fA-F]+)(\.[0-9a-fA-F]*)?([pP]-?[0-9]+)?$
    program = ""
    with open(fname, "r") as ins:
        for line in ins:
            program += line

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
    i, tokens = doIt(i, tokens)
    print("Output:",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])


def doIt(i, tokens):
    i, tokens = chunk(i, tokens)
    i, tokens = matchTypeNow(i, tokens, "EOF")
    return i, tokens

def exp_p(i, tokens):
    i, tokens = optional(i, tokens, [(binop,MATCH_FUNCTION),(exp,MATCH_FUNCTION),(exp_p,MATCH_FUNCTION)], 1)
    return i, tokens

def stat_for(i, tokens):
    if contains(i, tokens, [("Name",MATCH_TYPE)]) and contains(i+1, tokens, [("=",MATCH_VALUE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
        print("Equals in stat_for, Name",i)
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, ",")
        i, tokens = exp(i, tokens)
        i, tokens = optional(i, tokens, [(",",MATCH_VALUE),(exp,MATCH_FUNCTION)], 1)
        i, tokens = matchValueNow(i, tokens, "do")
        i, tokens = block(i, tokens)
        i, tokens = matchValueNow(i, tokens, "end")
    elif contains(i, tokens, firstSets["namelist"]) and contains(i+1, tokens, [(",",MATCH_VALUE),("in",MATCH_VALUE)]):
        i, tokens = namelist(i, tokens)
        i, tokens = matchValueNow(i, tokens, "in")
        i, tokens = explist(i, tokens)
        i, tokens = matchValueNow(i, tokens, "do")
        i, tokens = block(i, tokens)
        i, tokens = matchValueNow(i, tokens, "end")
    return i, tokens

def stat_local(i, tokens):
    if contains(i, tokens, [("function",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "function")
        i, tokens = matchTypeNow(i, tokens, "Name")
        error("Going from stat_local to funcbody",i)
        i, tokens = funcbody(i, tokens)
        error("Returned from funcbody, to stat_local",i)
    elif contains(i, tokens, firstSets["namelist"]):
        i, tokens = namelist(i, tokens)
        i, tokens = optional(i, tokens,[("=",MATCH_VALUE),(explist,MATCH_FUNCTION)], 1)
    return i, tokens

def stat(i, tokens):
    global varnames
    global expnames
    global recent_parameter_list
    print("HI we're in stat",i)
    if contains(i, tokens, firstSets["varlist"]) and contains(i+1, tokens, [("=",MATCH_VALUE), ("[",MATCH_VALUE), (",",MATCH_VALUE)]):
        #print("Hi from inside first varist",i)
        original_i = i
        i, tokens = varlist(i, tokens)
        #print("Hi the VARNAMES is :::::::::",varnames)
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = explist(i, tokens)
        #print("Hi the EXPLIST is ;;;;;;;;;",expnames)
        for j, (a,b) in enumerate(expnames):
            if a == -1 and b == -1:
                recent_parameter_list.insert( j , (-1,-1) )
        #print("HI the func args are -------",recent_parameter_list)
        try:
            n = len(varnames)
            for j in range(0, n):
                if expnames[j][0] != -1:
                    varname = varnames[j]
                    params = recent_parameter_list[j]
                    name_str = ""
                    args_str = ""
                    for k in range(varname[0], varname[1]):
                        name_str += tokens[k].value
                    for k in range(params[0], params[1]):
                        args_str += tokens[k].value
                    print(name_str,args_str)
        except IndexError:
            error("Could not parse the function header")
        varnames = []
        expnames = []
        recent_parameter_list = []
    elif contains(i, tokens, firstSets["functioncall"]) and contains(i+1, tokens, firstSets["exp_args_back"]+firstSets["args_back"]):
        i, tokens = functioncall(i, tokens)
    elif contains(i, tokens, [("do",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "do")
        i, tokens = matchValueNow(i, tokens, "block")
        i, tokens = matchValueNow(i, tokens, "end")
    elif contains(i, tokens, [("while",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "while")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, "do")
        i, tokens = block(i, tokens)
        i, tokens = matchValueNow(i, tokens, "end")
    elif contains(i, tokens, [("repeat",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "repeat")
        i, tokens = block(i, tokens)
        i, tokens = matchValueNow(i, tokens, "until")
        i, tokens = exp(i, tokens)
    elif contains(i, tokens, [("if",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "if")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, "then")
        i, tokens = block(i, tokens)
        i, tokens = star(i, tokens, [("elseif",MATCH_VALUE),(exp,MATCH_FUNCTION),("then",MATCH_VALUE),(block,MATCH_FUNCTION)], 1)
        i, tokens = optional(i, tokens, [("else",MATCH_VALUE),(block,MATCH_FUNCTION)], 1)
        i, tokens = matchValueNow(i, tokens, "end")
    elif contains(i, tokens, [("for",MATCH_VALUE)]):
        error("Start of for:",tokens[i],i)
        i, tokens = matchValueNow(i, tokens, "for")
        i, tokens = stat_for(i, tokens)
        error("End of for:",tokens[i],i)
    elif contains(i, tokens, [("function",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "function")
        i_b = i
        i, tokens = funcname(i, tokens)
        varnames.append( (i_b,i) )
        expnames.append( (0,0) )
        i, tokens = funcbody(i, tokens)
    elif contains(i, tokens, [("local",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "local")
        i, tokens = stat_local(i, tokens)
    
    return i, tokens

def functiondef(i, tokens):
    original_i = i
    i, tokens = matchValueNow(i, tokens, "function")
    # to find a = function(b) end
    if match_v(tokens, original_i-1, "="):
        # if an equals behind us
        print("fooe AHA HAHA HAH SO APPEASING\n\n\n\n")
    error("Going from func def to funcbody",i)
    i, tokens = funcbody(i, tokens)
    error("Back from funcbody to func def",i)
    return i, tokens

def funcbody(i, tokens):
    error("Entered funcbody",i)
    i, tokens = matchValueNow(i, tokens, "(")
    i, tokens = optional(i, tokens, [(parlist,MATCH_FUNCTION)], 1)
    i, tokens = matchValueNow(i, tokens, ")")
    i, tokens = block(i, tokens)
    i, tokens = matchValueNow(i, tokens, "end")
    error("Leaving funcbody",i)
    return i, tokens

def block(i, tokens):
    i, tokens = chunk(i, tokens)
    return i, tokens

def chunk(i, tokens):
    my_i = i
    error("Chunk called with i as",i,"(",my_i,")")
    i, tokens = star(i, tokens, [(stat,MATCH_FUNCTION),
        (optional_curry([(";",MATCH_VALUE)],1),MATCH_FUNCTION)], 1)
    i, tokens = optional(i, tokens, [(laststat,MATCH_FUNCTION),
        (optional_curry([(";",MATCH_VALUE)],1),MATCH_FUNCTION)], 1)
    error("Chunk finishing with i as",i,"(",my_i,")")
    return i, tokens

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
    original_i = i
    print("In a varlist",i)
    i, tokens = var(i, tokens)
    print("First mandatory var is",original_i,tokens[original_i])
    i, tokens = star(i, tokens, [(",",MATCH_VALUE),(var,MATCH_FUNCTION)], 2)
    print("End of varlist",i)
    return i, tokens

def var(i, tokens):
    global varnames
    original_i = i
    if contains(i, tokens, firstSets["exp_front"]):
        i, tokens = exp_front(i, tokens)
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
        i, tokens = exp_back(i, tokens)
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
    varnames.append( (original_i,i) ) # note down the variable
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
        print("\n")
        print("In exp back start",tokens[i],i)
        i, tokens = matchValueNow(i, tokens, "[")
        print("In exp back matched [",tokens[i],i)
        i, tokens = exp(i, tokens)
        print("In exp back exp",tokens[i],i)
        i, tokens = matchValueNow(i, tokens, "]")
        print("In exp_back leaving",tokens[i],i)
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
    error("Starting explist",i)
    i, tokens = exp(i, tokens)
    error("In explist, done with first exp",i)
    i, tokens = star(i, tokens, [(",",MATCH_VALUE),(exp,MATCH_FUNCTION)], 2)
    error("Leaving explist",i)
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
        print("Equals in field, in [",i)
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
        print("Equals in field, in Name",i)
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
    elif contains(i, tokens, firstSets["exp"]):
        i, tokens = exp(i, tokens)
    return i, tokens

def exp(i, tokens):
    global expnames
    error("Starting exp",i)
    isFunc = False
    original_i = i
    if contains(i, tokens, [("nil",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "nil")
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, [("false",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "false")
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, [("true",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "true")
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, [("Number",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Number")
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, [("String",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "String")
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, [("...",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "...")
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, firstSets["functiondef"]):
        isFunc = True
        print("Start of func in exp list",i)
        i, tokens = functiondef(i, tokens)
        funcEnd_i = i
        print("Func defined in exp list",i)
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, firstSets["prefixexp"]):
        i, tokens = prefixexp(i, tokens)
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, firstSets["tableconstructor"]):
        i, tokens = tableconstructor(i, tokens)
        i, tokens = exp_p(i, tokens)
    elif contains(i, tokens, firstSets["unop"]):
        i, tokens = unop(i, tokens)
        i, tokens = exp(i, tokens)
        i, tokens = exp_p(i, tokens)
    if isFunc:
        expnames.append( (original_i,funcEnd_i) )
    else:
        expnames.append( (-1,-1) )
    error("Returning from exp",i)
    #traceback.print_exc()
    return i, tokens

def funcname(i, tokens):
    i, tokens = matchTypeNow(i,tokens,"Name")
    i, tokens = star(i, tokens, [(".",MATCH_VALUE), ("Name",MATCH_TYPE)], 2)
    i, tokens = optional(i, tokens, [(":",MATCH_VALUE), ("Name",MATCH_TYPE)], 2)
    return i, tokens

def parlist(i, tokens):
    global recent_parameter_list
    i_b = i
    # chosen the ... only
    if contains(i, tokens, [("...",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "...")
    # namelist
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = namelist(i, tokens)
        i, tokens = optional(i, tokens, [(",",MATCH_VALUE),("...",MATCH_VALUE)], 2)
    recent_parameter_list.append( (i_b,i) )
    print("Function:",[str(t.type)+": "+str(t.value) for t in tokens[i_b:i]])
    
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

def matchTerminalListError(i, tokens, list, err):
    i_b = i
    i, tokens = matchTerminalInList(i, tokens, list)
    #if i == i_b:
        #error(err)
    return i, tokens

def matchTerminalInList(i, tokens, list):
    for op in list:
        if lookahead(i, tokens, [op], 1):
            i, tokens = matchValueNow(i, tokens, op[0])
            break
    return i, tokens

def matchTypeNow(i, tokens, type):
    b = matchType(type)(i,tokens)
    if b:
        #print("Matched",i," to ",type)
        pass
    return b

def matchValueNow(i, tokens, value):
    b = matchValue(value)(i,tokens)
    if b:
        #print("Matched",i," to ",value)
        pass
    return b

def matchType(type):
    def f(i, tokens):
        if match_t(tokens,i,type):
            i += 1
        return i, tokens
    # for nice error error
    f.__name__ = type
    return f

def matchValue(value):
    def f(i, tokens):
        if match_v(tokens,i,value):
            i += 1
        return i, tokens
    # for nice error error
    f.__name__ = value
    return f

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

# lookahead function right here
def lookahead(i, tokens, func_tuples, lookahead_n):
    global errors_switch
    errors_switch += 1
    for j in range(0, min(len(func_tuples),lookahead_n)):
        b = False
        if func_tuples[j][1] == MATCH_VALUE:
            b = match_v(tokens, i+j, func_tuples[j][0])
        elif func_tuples[j][1] == MATCH_TYPE:
            b = match_t(tokens, i+j, func_tuples[j][0])
        elif func_tuples[j][1] == MATCH_FUNCTION:
            firstSet = firstSets[func_tuples[j][0].__name__]
            b = contains(i+j, tokens, firstSet)
            #b = i_changed(i+j, tokens, func_tuples[j][0])
        if not b:
            errors_switch -= 1
            return False
    errors_switch -= 1
    return True

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

def optional_curry(func_tuples, lookahead):
    def f(i, tokens):
        return something(i, tokens, func_tuples, lookahead, optional_do)
    return f

def optional(i, tokens, func_tuples, lookahead):
    return something(i, tokens, func_tuples, lookahead, optional_do)

def star(i, tokens, func_tuples, lookahead):
    org_i = i
    i, tokens = something(i, tokens, func_tuples, lookahead, star_do)
    if i < org_i:
        raise ValueError("Ahhhh, i got lower?")
    return i, tokens

def match_t(tokens,i,type):
    return i >= 0 and i < len(tokens) and tokens[i].type == type

def match_v(tokens,i,val):
    return i >= 0 and i < len(tokens) and tokens[i].value == val

if __name__ == "__main__":
    parse(sys.argv[1])
