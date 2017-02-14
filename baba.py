#!/usr/bin/env python3

import collections
import re
import copy
import sys
import traceback

Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

# function adapted from https://docs.python.org/3.4/library/re.html#writing-a-tokenizer
# takes input program as a string and turns it into tokens
# yields these tokens so they may be processed
# token have line/column of item, as well as a type
# and the value of the item, eg. a variable name has
# value 'foo' and type 'Name
# a number has type 'Number' and value '69.'
def tokenize(code):
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
            ("LongString", r'\[(?P<longString>=*)\[(.|\n)*?\](?P=longString)\]'),
            ("Number", r'0[xX]([0-9a-fA-F]*)(\.[0-9a-fA-F]+)([pP]-?[0-9]+)?|0[xX]([0-9a-fA-F]+)(\.[0-9a-fA-F]*)?([pP]-?[0-9]+)?|([0-9]+)(\.[0-9]*)?([eE]-?[0-9]+)?|([0-9]*)(\.[0-9]+)([eE]-?[0-9]+)?' ),
            ("Name", r'[_a-zA-Z][_a-zA-Z0-9]*'), # should be before keyword
            ("Keyword", keywords_regex),
            ("Operator", operators_regex),
            ("String", r'\"([^\"\\]|\\.)*\"|\'([^\'\\]|\\.)*\''),
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
            raise RuntimeError('%r unexpected on line %d, could not interpret token' % (value, line_number))
        else:
            if kind == "String" and value:
                value = value[1:-1] # remove first and last chars - quote marks
            elif kind == "LongString" and value:
                # strip [==[ from start of long string
                num_square_brackets = 0
                prefix_suffix = 0
                for v in value:
                    prefix_suffix += 1
                    if v == "[":
                        num_square_brackets += 1
                    if num_square_brackets == 2:
                        value = value[prefix_suffix:]
                        # strip newline if first char
                        if value[0] == '\n':
                            value = value[1:]
                        break

                # strip ]==] from end of long string
                value = value[:len(value)-prefix_suffix]
                kind = "String"
                pass
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
# used to turn off error logging when matching terminals
# but whilst looking ahead, as a non-match there is not an error
# when 0 errors are not logged, when entering lookahead function
# switch inced, when leaving switch decremented

ANON = -1
# anonymous func in tuple list position in token list
# i can never be -1, so then will know it was an anon func

ANONYMOUS_FUNCTION = "anonymous function"
# pretty print for anonymous function

function_name_list = []
function_params_list = []
# both of these are tuples that are the things named
# these are used to put tuples that are token positions in
# so later the function arguments and names can be used

firstSets["binop"] = [('+',MATCH_VALUE), ('-',MATCH_VALUE), ('*',MATCH_VALUE), ('/',MATCH_VALUE), ('^',MATCH_VALUE), ('%',MATCH_VALUE), ('..',MATCH_VALUE), ('<',MATCH_VALUE), ('<=',MATCH_VALUE), ('>',MATCH_VALUE), ('>=',MATCH_VALUE), ('==',MATCH_VALUE), ('~=',MATCH_VALUE), ('and',MATCH_VALUE), ('or',MATCH_VALUE)]
firstSets["exp"] = [('nil',MATCH_VALUE),('false',MATCH_VALUE),('true',MATCH_VALUE),('Number', MATCH_TYPE), ('String', MATCH_TYPE), ('...', MATCH_VALUE),('function',MATCH_VALUE),('(',MATCH_VALUE),('{',MATCH_VALUE),('Name',MATCH_TYPE),('-',MATCH_VALUE),('not',MATCH_VALUE),('#',MATCH_VALUE)]
firstSets["stat_local"] = [('Name',MATCH_TYPE),('function',MATCH_VALUE)]
firstSets["stat_for"] = [('Name',MATCH_TYPE)]
firstSets["functiondef"] = [('function',MATCH_VALUE)]
firstSets["funcbody"] = [('(',MATCH_VALUE)]
firstSets["laststat"] = [('return',MATCH_VALUE),('break',MATCH_VALUE)]
firstSets["prefixexp"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]
firstSets["exp_front"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)]
firstSets["var"] = [('Name',MATCH_TYPE)] + firstSets["exp_front"]
firstSets["stat"] = [('Name',MATCH_TYPE),('(',MATCH_VALUE)] + [('do',MATCH_VALUE), ('while',MATCH_VALUE), ('repeat',MATCH_VALUE), ('if',MATCH_VALUE), ('for',MATCH_VALUE), ('function',MATCH_VALUE), ('local',MATCH_VALUE)]
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
firstSets["end_explist"] = [(",",MATCH_VALUE),("=",MATCH_VALUE)]
firstSets["stat_name_eap"] = firstSets["exp_back"] + firstSets["args_back"]
firstSets["stat_name"] = firstSets["stat_name_eap"] + firstSets["end_explist"]

# appends start and end index of function name to function_name_list
# ie. (ANON,ANON) -> anon function
# (5,6) -> function bla where bla at 5
# (5 8) -> function bla.blabla
def log_function_name(start_i, end_i):
    global function_name_list
    function_name_list.append( (start_i, end_i) )

# same as above but for logging function parameters
def log_params(start_i, end_i):
    print("Logging params",start_i,end_i)
    global function_params_list
    function_params_list.append( (start_i, end_i) )

# function to take error and print it
# only if errors switch is 0
def error(i_tup,tokens,*err):
    global errors_switch
    if errors_switch == 0:
        s = ""
        err_line = tokens[i_tup[0]].line
        err_col = tokens[i_tup[0]].column
        for item in err:
            s += item
        print("Error:",s,"on line",err_line,"at col",err_col)

# why predictive parsing, faster

def parse(fname):
    # follow(exp) = firstSets["exp_p"] - firstSets["binop"]

    ## add followset of stat to exp_p
    ## add followset of chunk to exp_p
    ## add followset of field to exp_p
    ## add followset of explist to exp_p
    ## add followset of stat_local to exp_p
    ## add followset of laststat to exp_p

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

    if len(function_name_list) != len(function_params_list):
        # we're screwed, errors so function declares and
        # func params don't line up, so we don't know
        print("Length of functions name list does not match that of params list")
        pass
    else:
        print("Printing functions")
        n = len(function_name_list)
        for j in range(0, n):
            f_name = ""
            params = ""
            line = ""
            line += str(tokens[function_name_list[j][0]].line)
            # name of function
            if function_name_list[j][0] == ANON or function_name_list[j][1] == ANON:
                # anon function
                f_name += ANONYMOUS_FUNCTION
            else:
                for k in range(function_name_list[j][0],
                        function_name_list[j][1]):
                    f_name += tokens[k].value

            # params list string
            params += "("
            for k in range(function_params_list[j][0],
                    function_params_list[j][1]):
                params += tokens[k].value
            params += ")"
            print("Line:",line,f_name,params)
    #function_name_list = []
    #function_params_list = []

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
    print("In stat local",i)
    if contains(i, tokens, [("function",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "function")
        i_b = i
        i, tokens = matchTypeNow(i, tokens, "Name")
        log_function_name(i_b,i)
        i, tokens = funcbody(i, tokens)
    elif contains(i, tokens, firstSets["namelist"]):
        i, tokens = namelist(i, tokens)
        i, tokens = optional(i, tokens,[("=",MATCH_VALUE),(explist,MATCH_FUNCTION)], 1)
    else:
        error((i,i), tokens, "Expected function declaration or variable name")
    return i, tokens

def stat_name(i, tokens):
    print("Welcome to the real world of stat_name",i)
    if contains(i, tokens, firstSets["stat_name_eap"]):
        i, tokens = stat_name_eap(i, tokens)
    elif contains(i, tokens, firstSets["end_explist"]):
        print("In stat name, should be going to end_explist",i)
        i, tokens = end_explist(i, tokens)
        print("Done with stat_name_explist",i)
    return i, tokens

def stat_name_eap(i, tokens):
    if contains(i, tokens, firstSets["exp_back"]):
        i, tokens = exp_back(i, tokens)
        i, tokens = end_explist(i, tokens)
    elif contains(i, tokens, firstSets["args_back"]):
        i, tokens = args_back(i, tokens)
    return i, tokens

def end_explist(i, tokens):
    print("In end_explist",i)
    i, tokens = star(i, tokens, [(",",MATCH_VALUE),(var,MATCH_FUNCTION)], 1)
    print("In end_explist, done with star(,var) matches",i)
    i, tokens = matchValueNow(i, tokens, "=")
    print("In end_explist, matched = ",i)
    i, tokens = explist(i, tokens)
    print("In end_explist exiting, end",i)
    return i, tokens

def stat(i, tokens):
    print("In stat",i)
    if contains(i, tokens, [("Name",MATCH_TYPE)]):
        print("In name in stat",i)
        i, tokens = matchTypeNow(i, tokens, "Name")
        print("\tMatched name in stat",i)
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1, 1)
        print("\tDone stat in exp_args_back in stat",i)
        i, tokens = stat_name(i, tokens)
        print("Done stat_name in stat",i)
    elif contains(i, tokens, [("(",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "(")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, ")")
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1, 1)
        i, tokens = stat_name_eap(i, tokens)
    elif contains(i, tokens, [("do",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "do")
        i, tokens = block(i, tokens)
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
        i, tokens = matchValueNow(i, tokens, "for")
        i, tokens = stat_for(i, tokens)
    elif contains(i, tokens, [("function",MATCH_VALUE)]):
        print("In stat in function",i)
        i, tokens = matchValueNow(i, tokens, "function")
        i_b = i
        i, tokens = funcname(i, tokens)
        log_function_name(i_b, i)
        i, tokens = funcbody(i, tokens)
        print("Out stat in function",i)
    elif contains(i, tokens, [("local",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "local")
        i, tokens = stat_local(i, tokens)
    else:
        #error("Error in statement",tokens[i])
        pass
    
    return i, tokens

def functiondef(i, tokens):
    i_b = i
    print("In func def")
    i, tokens = matchValueNow(i, tokens, "function")
    log_function_name(i_b, ANON)
    i, tokens = funcbody(i, tokens)
    print("Out func def")
    return i, tokens

def funcbody(i, tokens):
    i, tokens = matchValueNow(i, tokens, "(")
    i_b = i
    i, tokens = optional(i, tokens, [(parlist,MATCH_FUNCTION)], 1)
    log_params(i_b, i)
    i, tokens = matchValueNow(i, tokens, ")")
    i, tokens = block(i, tokens)
    i, tokens = matchValueNow(i, tokens, "end")
    return i, tokens

def block(i, tokens):
    i, tokens = chunk(i, tokens)
    return i, tokens

def chunk(i, tokens):
    my_i = i
    print("In chunk, calling stat star",i)
    i, tokens = star(i, tokens, [(stat,MATCH_FUNCTION),
        (optional_curry([(";",MATCH_VALUE)],1),MATCH_FUNCTION)], 1)
    print("Finished chunk star of stat",i)
    i, tokens = optional(i, tokens, [(laststat,MATCH_FUNCTION),
        (optional_curry([(";",MATCH_VALUE)],1),MATCH_FUNCTION)], 1)
    print("Leaving chunk",i)
    return i, tokens

def laststat(i, tokens):
    if contains(i, tokens, [("return",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "return")
        i, tokens = optional(i, tokens, [(explist,MATCH_FUNCTION)], 1)
    elif contains(i, tokens, [("break",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "break")

    return i, tokens

def prefixexp(i, tokens):
    print("Entered prefixexp",i)
    if contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "Name")
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
    elif contains(i, tokens, [("(",MATCH_VALUE)]):
        print("In prefixexp, in bracket 2nd",i)
        i, tokens = matchValueNow(i, tokens, "(")
        print("In prefixexp, matched bracket",i)
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, ")")
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1)
    return i, tokens

def var(i, tokens):
    original_i = i
    print("In var")
    if contains(i, tokens, [("Name",MATCH_TYPE)]) and contains(i+1, tokens, [(",", MATCH_VALUE), ("=", MATCH_VALUE)]):
        print("I'm actually never picked - kappa")
        i, tokens = matchTypeNow(i, tokens, "Name")
    elif contains(i, tokens, firstSets["exp_front"]):
        print("In var, matched exp_front")
        i, tokens = exp_front(i, tokens)
        print("Done exp_front",i)
        i, tokens = star(i, tokens, [(exp_args_back,MATCH_FUNCTION)], 1, 1)
        print("Done exp_front",i)
        i, tokens = exp_back(i, tokens)
        print("Done exp_back that never happens, see i",i)
    return i, tokens

def exp_args_back(i, tokens):
    print("In exp_args_back",i)
    if contains(i, tokens, firstSets["exp_back"]):
        print("Going from exp_args_back into exp_back",i)
        i, tokens = exp_back(i, tokens)
    elif contains(i, tokens, firstSets["args_back"]):
        print("Going from exp_args_back into args_back",i)
        i, tokens = args_back(i, tokens)
        print("DOne with args_back in exp_args_back",i)
    print("Exiting exp_args_back",i)
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
    print("In exp_back",i)
    if contains(i, tokens, [("[",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "[")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, "]")
    elif contains(i, tokens, [(".",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, ".")
        i, tokens = matchTypeNow(i, tokens, "Name")
    print("Out exp_back",i)
    return i, tokens

def args_back(i, tokens):
    print("In args_back",i)
    if contains(i, tokens, firstSets["args"]):
        print("GOING from args_back to args",i)
        i, tokens = args(i, tokens)
    elif contains(i, tokens, [(":",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, ":")
        i, tokens = matchTypeNow(i, tokens, "Name")
        i, tokens = args(i, tokens)
    print("Leaving args_back",i)
    return i, tokens

def args(i, tokens):
    print("In args",i)
    if contains(i, tokens, [("(",MATCH_VALUE)]):
        print("In args, matching ( ",i)
        i, tokens = matchValueNow(i, tokens, "(")
        print("In args, matchED (, now doing explist ",i)
        i, tokens = optional(i, tokens, [(explist,MATCH_FUNCTION)], 1)
        print("In args, DONE WITH matchED explist ",i)
        i, tokens = matchValueNow(i, tokens, ")")
    elif contains(i, tokens, firstSets["tableconstructor"]):
        i, tokens = tableconstructor(i, tokens)
    elif contains(i, tokens, [("String",MATCH_TYPE)]):
        i, tokens = matchTypeNow(i, tokens, "String")
    print("Out args",i)
    return i, tokens

def explist(i, tokens):
    i_b = i
    print("---------Entering explist",i,"(",i_b,")")
    i, tokens = exp(i, tokens)
    print("In explist, have done exp, about to do star",i)
    i, tokens = star(i, tokens, [(",",MATCH_VALUE),(exp,MATCH_FUNCTION)], 2)
    print("---------Exiting explist",i,"(",i_b,")")
    return i, tokens

def tableconstructor(i, tokens):
    print("In tablecons",i)
    i, tokens = matchValueNow(i, tokens, "{")
    print("Enter optional fieldlist",i)
    i, tokens = optional(i, tokens, [(fieldlist,MATCH_FUNCTION)], 1)
    print("Out of optional fieldlist",i)
    i, tokens = matchValueNow(i, tokens, "}")
    print("Out tablecons",i)
    return i, tokens

def fieldlist(i, tokens):
    i, tokens = field(i, tokens)
    i, tokens = star(i, tokens, [(fieldsep,MATCH_FUNCTION),(field,MATCH_FUNCTION)], 2)
    i, tokens = optional(i, tokens, [(fieldsep,MATCH_FUNCTION)], 1)
    return i, tokens

def field(i, tokens):
    print("In field",i)
    if contains(i, tokens, [("[",MATCH_VALUE)]):
        # todo, fill the aftermath of each of these
        # with checks and should haves
        i, tokens = matchValueNow(i, tokens, "[")
        i, tokens = exp(i, tokens)
        i, tokens = matchValueNow(i, tokens, "]")
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
    elif contains(i, tokens, [("Name",MATCH_TYPE)]) and contains(i+1, tokens, [("=",MATCH_VALUE)]):
        # need lookahead 2 to decide if going to Name and then = or
        # just exp that can be Name
        print("In name in field",i)
        i, tokens = matchTypeNow(i, tokens, "Name")
        i, tokens = matchValueNow(i, tokens, "=")
        i, tokens = exp(i, tokens)
        print("Out name in field",i)
    elif contains(i, tokens, firstSets["exp"]):
        i, tokens = exp(i, tokens)
    print("Out field",i)
    return i, tokens

def exp(i, tokens):
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
        i, tokens = functiondef(i, tokens)
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
    return i, tokens

def funcname(i, tokens):
    i, tokens = matchTypeNow(i,tokens,"Name")
    i, tokens = star(i, tokens, [(".",MATCH_VALUE), ("Name",MATCH_TYPE)], 1)
    i, tokens = optional(i, tokens, [(":",MATCH_VALUE), ("Name",MATCH_TYPE)], 1)
    return i, tokens

def parlist(i, tokens):
    i_b = i
    # chosen the ... only
    if contains(i, tokens, [("...",MATCH_VALUE)]):
        i, tokens = matchValueNow(i, tokens, "...")
    # namelist
    elif contains(i, tokens, [("Name",MATCH_TYPE)]):
        i, tokens = namelist(i, tokens)
        i, tokens = optional(i, tokens, [(",",MATCH_VALUE),("...",MATCH_VALUE)], 1)
    return i, tokens

def namelist(i, tokens):
    i, tokens = matchTypeNow(i,tokens,"Name")
    i, tokens = star(i, tokens, [(",",MATCH_VALUE), ("Name",MATCH_TYPE)], 2)
    return i, tokens

def binop(i, tokens):
    return matchTerminalInList(i, tokens, firstSets["binop"])

def unop(i, tokens):
    return matchTerminalInList(i, tokens, firstSets["unop"])

def fieldsep(i, tokens):
    return matchTerminalInList(i, tokens, firstSets["fieldsep"])

def matchTerminalInList(i, tokens, list):
    for op in list:
        if contains(i, tokens, [op]):
            i, tokens = matchValueNow(i, tokens, op[0])
            break
    return i, tokens

def matchTypeNow(i, tokens, type):
    b = matchType(type)(i,tokens)
    return b

def matchValueNow(i, tokens, value):
    b = matchValue(value)(i,tokens)
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
    global errors_switch
    errors_switch += 1
    # don't want errors printed here as checking
    for _, (val,match_type) in enumerate(firstSet):
        b = False
        if match_type == MATCH_VALUE:
            b = match_v(tokens, i, val)
        elif match_type == MATCH_TYPE:
            b = match_t(tokens, i, val)
        if b:
            errors_switch -= 1
            return True
    errors_switch -= 1
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
        if not b:
            errors_switch -= 1
            return False
    errors_switch -= 1
    return True

def something(i, tokens, func_tuples, lookahead_n, repeater, lookback=0):
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
    i_series = []
    if lookahead(i, tokens, func_tuples, lookahead_n):
        i_series.append(i)
        for i, tokens in repeater(i, tokens, funcs):
            i_series.append(i)

            # next iter
            if not lookahead(i, tokens, func_tuples, lookahead_n):
                # we're breaking
                i = i_series[max(0,len(i_series)-1-lookback)]
                break
    else:
        pass
        # if no match at all
        #return i, tokens
    # we always break instantly according to printouts?

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

def star(i, tokens, func_tuples, lookahead, lookback=0):
    org_i = i
    i, tokens = something(i, tokens, func_tuples, lookahead, star_do, lookback)
    if i < org_i:
        raise ValueError("Ahhhh, i got lower?")
    return i, tokens

def match_t(tokens,i,type):
    #error("Type:Trying to match",tokens[i].type,"to",type)
    b = i >= 0 and i < len(tokens) and tokens[i].type == type
    if not b:
        error((i,i),tokens,"Expected-type '",type,"' but got '",tokens[i].value,"' of type '",tokens[i].type,"'")
    return b

def match_v(tokens,i,val):
    #error("Val:Trying to match",tokens[i].value,"to",val)
    b = i >= 0 and i < len(tokens) and tokens[i].value == val
    if not b:
        error((i,i),tokens,"Expected-value '",val,"' but got '",tokens[i].value,"'")
    return b

if __name__ == "__main__":
    parse(sys.argv[1])
