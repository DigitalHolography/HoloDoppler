function [HRES, rValue ] = PhGetVersion(CN, verSelection)
%Parameters:
%verSelection - use constants class for options values

[HRES,rValue] = calllib('phcon','PhGetVersion',CN,verSelection,0);
OutputError(HRES);

end

