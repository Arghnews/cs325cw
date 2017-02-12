#!/usr/bin/env python3

import re
import copy

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
