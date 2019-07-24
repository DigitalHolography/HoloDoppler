function [HRES,cnt,bitDepths] = PhGetBitDepths(CN)

pBitDepths = libpointer('uint32Ptr',zeros(5,1));%8,10,12,14,16
[HRES, cnt, bitDepths] = calllib('phcon','PhGetBitDepths',CN, 0, pBitDepths);
OutputError(HRES);

end

