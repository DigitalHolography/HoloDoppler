function [ HRES ] = PhGet(CN, Selector, pVal)
%pVal is a libpointer to the desired information

[HRES, dummy] = calllib('phcon', 'PhGet', CN, Selector, pVal);
OutputError(HRES);

end

