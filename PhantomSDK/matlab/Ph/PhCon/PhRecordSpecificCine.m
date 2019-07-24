function [HRES] = PhRecordSpecificCine(CN, cineNr)

HRES = calllib('phcon','PhRecordSpecificCine',CN,cineNr);
OutputError(HRES);

end

