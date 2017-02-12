# * -> stat_c, ? -> stat_s

# chunk ::= {stat [`;´]} [laststat [`;´]]
chunk ::= chunk_c chunk_s2
chunk_c ::= stat chunk_s1 chunk_c | epsilon
chunk_s1 ::= `;´ | epsilon
chunk_s2 ::= laststat chunk_s1 | epsilon

block ::= chunk

# stat ::= varlist `=´ explist | functioncall | do block end | while exp do block end | repeat block until exp | if exp then block {elseif exp then block} [else block] end | for Name `=´ exp `,´ exp [`,´ exp] do block end | for namelist in explist do block end | function funcname funcbody | local function Name funcbody | local namelist [`=´ explist] 
stat ::= varlist `=´ explist | functioncall | do block end | while exp do block end | repeat block until exp | if exp then block stat_c stat_s1 end | for Name `=´ exp `,´ exp stat_s2 do block end | for namelist in explist do block end | function funcname funcbody | local function Name funcbody | local namelist stat_s3
stat_c ::= elseif exp then block stat_c | epsilon
stat_s1 ::= else block | epsilon
stat_s2 ::= `,´ exp | epsilon
stat_s3 ::= `=´ explist | epsilon

# laststat ::= return [explist] | break
laststat ::= return laststat_s | break
laststat_s ::= explist | epsilon

# funcname ::= Name {`.´ Name} [`:´ Name]
funcname ::= Name funcname_c funcname_s
funcname_c ::= `.´ Name funcname_c | epsilon
funcname_s ::= `:´ Name | epsilon

# varlist ::= var {`,´ var}
varlist ::= var varlist_c
varlist_c ::= `,´ var varlist_c | epsilon

# var ::= Name | prefixexp `[´ exp `]´ | prefixexp `.´ Name 

var ::= 
    Name var_ |
    functioncall `[´ exp `]´ var_ |
    `(´ exp `)´ `[´ exp `]´ var_ |
    functioncall `.´ Name var_ |
    `(´ exp `)´ `.´ Name var_

var_ ::= 
    `[´ exp `]´ var_ |
    `.´ Name var_ |
    epsilon

prefixexp ::= 
    var prefixexp_ |
    `(´ exp `)´ prefixexp_ 

prefixexp_ ::=
    args prefixexp_ |
    `:´ Name args prefixexp_ |
    epsilon

functioncall ::=
    prefixexp args |
    prefixexp `:´ Name args 

# namelist ::= Name {`,´ Name}
namelist ::= Name namelist_c
namelist_c ::= `,´ Name namelist_c | epsilon

# explist ::= {exp `,´} exp
explist ::= explist_c exp
explist_c ::= exp `,´ explist_c | epsilon

# exp ::= nil | false | true | Number | String | `...´ | functiondef | prefixexp | tableconstructor | exp binop exp | unop exp 
exp ::= nil exp_ | false exp_ | true exp_ | Number exp_ | String exp_ | `...´ exp_ | functiondef exp_ | prefixexp exp_ | tableconstructor exp_ | unop exp exp_ 
exp_ ::= binop exp exp_ | epsilon

# prefixexp ::= var | functioncall | `(´ exp `)´

# args ::= `(´ [explist] `)´ | tableconstructor | String 
args ::= `(´ args_s `)´ | tableconstructor | String 
args_s ::= explist | epsilon

functiondef ::= function funcbody

# funcbody ::= `(´ [parlist] `)´ block end
funcbody ::= `(´ funcbody_s `)´ block end
funcbody_s ::= parlist | epsilon

# parlist ::= namelist [`,´ `...´] | `...´
parlist ::= namelist parlist_s | `...´
parlist_s ::= `,´ `...´ | epsilon

# tableconstructor ::= `{´ [fieldlist] `}´
tableconstructor ::= `{´ tableconstructor_s `}´
tableconstructor_s ::= fieldlist | epsilon

# fieldlist ::= field {fieldsep field} [fieldsep]
fieldlist ::= field fieldlist_c fieldlist_s
fieldlist_c ::= fieldsep field fieldlist_c | epsilon
fieldlist_s ::= fieldsep | epsilon

field ::= `[´ exp `]´ `=´ exp | Name `=´ exp | exp

fieldsep ::= `,´ | `;´

binop ::= `+´ | `-´ | `*´ | `/´ | `^´ | `%´ | `..´ | `<´ | `<=´ | `>´ | `>=´ | `==´ | `~=´ | and | or

unop ::= `-´ | not | `#´
