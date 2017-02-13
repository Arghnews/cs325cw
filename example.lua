local cookie = {}
local remy =  "remy"

function cookie.set(r, key, value, path)
	path = path or "/"
	if remy.detect(r) == remy.MODE_CGILUA then
		local ck =  "cgilua.cookies"
		return ck.set(key,value,{path=path})
	end
	r.headers_out['Set-Cookie'] = ("%s=%s;Path=%s;"):format(key, value, path)
end

function cookie.get(r, key)
	local remy_mode = remy.detect(r)
	if remy_mode == remy.MODE_CGILUA then
		local ck =  "cgilua.cookies"
		return ck.get(key)
	elseif remy_mode == remy.MODE_LWAN then
		return r.native_request:cookie(key)
	end
	return (r.headers_in['Cookie'] or ""):match(key .. "=([^;]+)") or ""
end

return cookie
