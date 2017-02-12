#!/usr/bin/env python3

import re

def main():

    # dict from string to symbols
    # dict from string to productions

    symbols = dict()
    productions = dict()

    with open("lua","r") as ins:
        lines = []
        for line in ins:
            if not re.match(r'^\s*$', line):
                lines.append(line.rstrip("\n"))

    delim = "::="
    comment = r'#'
    b_tick = r'`'
    f_tick = r'´'

    # add symbols
    for l in lines:
        pair = l.split(delim)
        symbol = pair[0]
        if symbol[0] == comment:
            continue
        # add non terminal
        symbol = symbol.strip()
        symbols[symbol] = Symbol(False,symbol)
        #print("Added symbol",symbols[symbol],"with key",symbol,len(symbol))

    for l in lines:
        pair = l.split(delim)
        name = pair[0]
        if name[0] == comment:
            continue
        sec = pair[1]
        for s in sec.split("|"):
            s = s.lstrip()
            lists = s.split()
            # A ::= Bb | c
            # l below is B,b, then c
            for l in lists: # each symbol in sublist
                symbol = l
                if l and l[0] == b_tick and l[-1] == f_tick:
                    symbol = l[1:-1]
                symbol = symbol.strip()
                is_in = symbol in symbols
                if not is_in:
                    #print("Terminal to add",symbol)
                    # add terminal
                    symbols[symbol] = Symbol(True,symbol)
        #productions[symbol] = Production(symbols[symbol],rhs_lists)

    for k, v in symbols.items():
        print(k," -> ", v)

class Symbol:
    def __init__(self,terminal,value):
        self.terminal = terminal
        self.value = value
        self.first_set = set()
        self.follow_set = set()

    def __str__(self):
        t = "(nt)"
        if self.terminal:
            t = "(t)"
        t = self.value + t
        return t

class Production:
    def __init__(self,LHS,RHS):
        self.LHS = LHS # symbol
        self.RHS = RHS # list of lists

if __name__ == "__main__":
    main()
