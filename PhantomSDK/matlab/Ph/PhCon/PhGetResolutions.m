function [ HRES, resCnt, resolutions] = PhGetResolutions( CN )
MAX_RES = 100;

% alloc memory for point array
point = get(libstruct('tagPOINT'));
for i=1:MAX_RES
    pointArray(i) = point;
end
pRes = libpointer('tagPOINT',pointArray);

[HRES, res, resCnt, dummy1, dummy2] = calllib('phcon', 'PhGetResolutions', CN, pRes, MAX_RES, libpointer, libpointer);
OutputError(HRES);

for i=1:resCnt
    resolutions(i) = get(pRes+(i-1),'Value');
end

end

