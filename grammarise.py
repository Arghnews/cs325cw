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

    nonterminal_order = []
    for k, v in symbols.items():
        #print(k," -> ", v)
        if not v.terminal:
            nonterminal_order.append(k)
        pass
    nonterminal_order.sort()
    print(nonterminal_order)

    for symbol, prod in list(productions.items()):
        continue
        #print(k," -> ", v)
        head = prod.LHS
        for rhs in prod.RHS:
            occurrences = 0
            for sym in rhs:
                if head.value == sym.value:
                    occurrences += 1
            if occurrences > 1:
                eliminate_direct_left_recursion(head,prod, symbols, productions)
                pass
    

def eliminate_indirect_left_recursion(nonterminal_order,symbols, productions):
    n = len(nonterminal_order)
    for i in range(0, n):
        Ai = productions[nonterminal_order[i]]
        for j in range(1, i):
            Aj = productions[nonterminal_order[j]]
            new_Ai_rhs = []
            for prod in Ai.RHS:
                gamma = copy.deepcopy(prod[1:])
                #print("Prod0:",prod[0])
                #print("Aj.LHS:",Aj.LHS)
                if Symbol.equal(prod[0],Aj.LHS):
                    for prod_list in Aj.RHS:
                        temp = copy.deepcopy(prod_list)
                        temp.append(gamma)
                        new_Ai_rhs.append(temp)  
                else:
                    new_Ai_rhs.append(copy.deepcopy(prod))
            #print("RHS b4 ",Ai.RHS)
            Ai.RHS = copy.deepcopy(new_Ai_rhs)
            #print("RHS aft",Ai.RHS)
        eliminate_direct_left_recursion(Ai.LHS,Ai,symbols,productions)

    #eliminate_direct_left_recursion(symbols,productions)

def eliminate_direct_left_recursion(head, prod, symbols, productions):
    new_head_name = head.value+"__"
    new_head = Symbol(head.terminal,new_head_name)
    list_lists = copy.deepcopy(prod.RHS)

    #print(list_lists)

    Alist = []
    Blist = []

    for l in list_lists:
        #print(l)
        if Symbol.equal(head,l[0]):
            Alist.append(copy.deepcopy(l[1:]))
            #pass # left recurse case
        else:
            Blist.append(copy.deepcopy(l))

    # append A` in both cases
    #print("Beta list",Blist)
    for b in Blist:
        b.append(copy.deepcopy(new_head))
    #print("Beta list",Blist)
    #print("Alpha list",Alist)
    for a in Alist:
        a.append(copy.deepcopy(new_head))
    # add epsilon
    Alist.append([symbols["epsilon"]])
    #print("Alpha list",Alist)

    # 1. build two new productions, head and head__
    # 2. insert both new prods
    # 3. overwrite head in symbol table and insert new head

    # 1.
    alpha = Production(copy.deepcopy(head),Blist)
    alpha_prime = Production(copy.deepcopy(new_head),Alist)

    # 2.
    #print("Current prod for ",head.value,productions[head.value])
    productions[head.value] = alpha
    productions[new_head.value] = alpha_prime
    #print("Head to",productions[head.value])
    #print("New helper func ",productions[new_head.value])

    # 3.
    #print("Symbols head b4 ",symbols[head.value])
    symbols[head.value] = head
    symbols[new_head.value] = new_head
    #print("Symbols head aft ",symbols[head.value])
    #print("Symbols new head aft ",symbols[new_head.value])

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
