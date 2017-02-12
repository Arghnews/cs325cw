#
#var ::=
    #Name |
    #prefixexp `[´ exp `]´ |
    #prefixexp `.´ Name
#
#prefixexp ::=
    #var |
    #functioncall |
    #`(´ exp `)´
#
#functioncall ::=
    #prefixexp args |
    #prefixexp `:´ Name args
#

#prefixexp ::=
    #var |
    #functioncall |
    #`(´ exp `)´

# fixed indirect by subbing var and functioncall into prefixexp

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

# left factoring in stat

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

# Fixing exp's direct recursion
exp ::= nil exp_1 | false exp_1 | true exp_1 | Number exp_1 | String exp_1 | `...´ exp_1 | functiondef exp_1 | prefixexp exp_1 | tableconstructor exp_1 | unop exp exp_1

exp_1 ::= binop exp exp_1 | epsilon
