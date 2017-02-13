function lmap(f, l)
	return delay(function()
		return cons(f(lcar(l)), lmap(f, lcdr(l)));
	end);
end;

function lmerge(a, b)
	return delay(function()
		local x, y = lcar(a), lcar(b);
		if x <= y then
			return cons(x, lmerge(lcdr(a), b));
		else
			return cons(y, lmerge(a, lcdr(b)));
		end;
	end);
end;

