function [ HRES ] = PhConfigPoolUpdate(period)

[HRES] = calllib('phcon', 'PhConfigPoolUpdate', period);
OutputError(HRES);

end

