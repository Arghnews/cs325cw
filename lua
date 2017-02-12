# * -> stat_c, ? -> stat_s

# chunk ::= {stat chunk_s1} chunk_s2
chunk_s1 ::= `;´ | epsilon
chunk_s2 ::= laststat chunk_s1 | epsilon

block ::= chunk

# stat ::= varlist `=´ explist | functioncall | do block end | while exp do block end | repeat block until exp | if exp then block {elseif exp then block} [else block] end | for Name `=´ exp `,´ exp [`,´ exp] do block end | for namelist in explist do block end | function funcname funcbody | local function Name funcbody | local namelist [`=´ explist] 
stat ::= varlist `=´ explist | functioncall | do block end | while exp do block end | repeat block until exp | if exp then block {elseif exp then block} stat_s1 end | for Name `=´ exp `,´ exp stat_s2 do block end | for namelist in explist do block end | function funcname funcbody | local function Name funcbody | local namelist stat_s3
stat_s1 ::= else block | epsilon
stat_s2 ::= `,´ exp | epsilon
stat_s3 ::= `=´ explist | epsilon

# laststat ::= return [explist] | break
laststat ::= return laststat_s | break
laststat_s ::= explist | epsilon

# funcname ::= Name {`.´ Name} [`:´ Name]
funcname ::= Name {`.´ Name} funcname_s
funcname_s ::= [`:´ Name] | epsilon

varlist ::= var {`,´ var}

var ::= Name | prefixexp `[´ exp `]´ | prefixexp `.´ Name 

namelist ::= Name {`,´ Name}

explist ::= {exp `,´} exp

exp ::= nil | false | true | Number | String | `...´ | functiondef | prefixexp | tableconstructor | exp binop exp | unop exp 

prefixexp ::= var | functioncall | `(´ exp `)´

functioncall ::= prefixexp args | prefixexp `:´ Name args 

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
fieldlist ::= field {fieldsep field} fieldlist_s
fieldlist_s ::= fieldsep | epsilon

field ::= `[´ exp `]´ `=´ exp | Name `=´ exp | exp

fieldsep ::= `,´ | `;´

binop ::= `+´ | `-´ | `*´ | `/´ | `^´ | `%´ | `..´ | `<´ | `<=´ | `>´ | `>=´ | `==´ | `~=´ | and | or

unop ::= `-´ | not | `#´
