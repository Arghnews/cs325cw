a = "a"
b = ''
d = 5.5
if{}{
iffy
    35.53e-53
    xx
    0x3aA.Ap-3
    e
function readonlytable(table)
    return setmetatable({}, {
    __index = table,
    __newindex = function(table, key, value)
    error("Attempt to modify read-only table")
    end,
    __metatable = false
    });
end
