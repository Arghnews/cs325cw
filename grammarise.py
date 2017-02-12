#!/usr/bin/env python3

import re
import copy

def main():

    # dict from string to symbols
    # dict from string to productions

    symbols = dict()
    productions = dict()

    lua = '''
    prefixexp ::= Name prefixexp_1 | `(´ exp `)´ prefixexp_1
    prefixexp_1 ::= `[´ exp `]´ prefixexp_1 | `.´ Name prefixexp_1 | args | prefixexp_1 | `:´ Name args prefixexp_1 | epsilon
    var ::= Name | prefixexp var_prefixexp
    var_prefixexp ::= `[´ exp `]´ | `.´ Name
    functioncall ::= prefixexp functioncall_prefixexp
    functioncall_prefixexp ::= args | `:´ Name args
    chunk ::= chunk_c chunk_s2
    chunk_c ::= stat chunk_s1 chunk_c | epsilon
    chunk_s1 ::= `;´| epsilon
    chunk_s2 ::= laststat chunk_s1 | epsilon
    block ::= chunk
    stat ::= varlist `=´ explist | functioncall | do block end | while exp do block end | repeat block until exp | if exp then block stat_c stat_s1 end | for stat_for | function funcname funcbody | local stat_local
    stat_for ::= Name `=´ exp `,´ exp stat_s2 do block end | namelist in explist do block end
    stat_local ::= function Name funcbody | namelist stat_s3
    stat_s1 ::= else block | epsilon
    stat_s2 ::= `,´ exp | epsilon
    stat_s3 ::= `=´ explist | epsilon
    stat_c ::= elseif exp then block stat_c | epsilon
    laststat ::= return laststat_s | break
    laststat_s ::= explist | epsilon
    funcname ::= Name funcname_c funcname_s
    funcname_s ::= `:´ Name | epsilon
    funcname_c ::= `.´ Name funcname_c | epsilon
    varlist ::= var varlist_c
    varlist_c ::= `,´ var varlist_c | epsilon
    namelist ::= Name namelist_c
    namelist_c ::= `,´ Name namelist_c | epsilon
    explist ::= explist_c exp
    explist_c ::= exp `,´ explist_c | epsilon
    args ::= `(´ args_s `)´ | tableconstructor | String
    args_s ::= explist | epsilon
    functiondef ::= function funcbody
    funcbody ::= `(´ funcbody_s `)´ block end
    funcbody_s ::= parlist | epsilon
    parlist ::= namelist parlist_s | `...´
    parlist_s ::= `,´ `...´ | epsilon
    tableconstructor ::= `{´ tableconstructor_s `}´
    tableconstructor_s ::= fieldlist | epsilon
    fieldlist ::= field fieldlist_c fieldlist_s
    fieldlist_s ::= fieldsep | epsilon
    fieldlist_c ::= fieldsep field fieldlist_c | epsilon
    field ::= `[´ exp `]´ `=´ exp | Name `=´ exp | exp
    fieldsep ::= `,´ | `;´
    binop ::= `+´ | `-´ | `*´ | `/´ | `^´ | `%´ | `..´ | `<´ | `<=´ | `>´ | `>=´ | `==´ | `~=´ | and | or
    unop ::= `-´ | not | `#´
    exp ::= nil exp_1 | false exp_1 | true exp_1 | Number exp_1 | String exp_1 | `...´ exp_1 | functiondef exp_1 | prefixexp exp_1 | tableconstructor exp_1 | unop exp exp_1
    exp_1 ::= binop exp exp_1 | epsilon
    '''

    lines = []
    for line in lua.splitlines():
        if not re.match(r'^\s*$', line):
            lines.append(line)

    delim = "::="
    comment = r'#'
    b_tick = r'`'
    f_tick = r'´'

    # add symbols
    for l in lines:
        print(l)
        pair = l.split(delim)
        symbol = pair[0]
        symbol = symbol.strip()
        if symbol[0] == comment:
            continue
        # add non terminal
        symbols[symbol] = Symbol(False,symbol)
        #print("Added symbol",symbols[symbol],"with key",symbol,len(symbol))

    for l in lines:
        pair = l.split(delim)
        name = pair[0].strip()
        if name[0] == comment:
            continue
        sec = pair[1]
        #print("Name",name)
        LHS = copy.deepcopy(symbols[name])
        #print("LHS:",LHS)
        RHS = []
        for s in sec.split("|"):
            s = s.lstrip()
            lists = s.split()
            # A ::= Bb | c
            # l below is B,b, then c
            sequence = []
            for l in lists: # each symbol in sublist
                symbol = l
                symbol = symbol.strip()
                if l and l[0] == b_tick and l[-1] == f_tick:
                    symbol = l[1:-1]
                is_in = symbol in symbols
                terminal = not is_in # non-t's in map already
                # add terminal
                if not is_in:
                    #print("Putting in",symbol,"as terminal",terminal)
                    symbols[symbol] = Symbol(terminal,symbol)
                else:
                    terminal = symbols[symbol].terminal
                #print("Appending",Symbol(terminal,symbol),"as terminal",terminal)
                sequence.append(Symbol(terminal,symbol))
            RHS.append(sequence)
        productions[name] = Production(LHS,RHS)
        #print("adding to prod",name)

    for k, v in productions.items():
        print(k, v)

class Symbol:

    b_tick = r'`'
    f_tick = r'´'

    @staticmethod
    def equal(s1,s2):
        return s1.value == s2.value

    def __init__(self,terminal,value):
        self.terminal = terminal
        self.value = value
        self.first_set = set()
        self.follow_set = set()

    def __str__(self):
        return self.toString()

    def toString(self):
        t = ""
        if self.terminal:
            t += Symbol.b_tick
            pass
        t += str(self.value)
        if self.terminal:
            t += Symbol.f_tick
            pass
        return t

    def __repr__(self):
        return self.toString()

class Production:
    def __init__(self,LHS,RHS):
        self.LHS = LHS # symbol
        self.RHS = RHS # list of lists

    def __str__(self):
        p = ""
        p += "LHS:" + str(self.LHS) + " to ["
        for o in self.RHS:
            p += " " + str(o)
        p += "]"
        return p

if __name__ == "__main__":
    main()
