function [ dlgRes ] = PhGetSaveCineName(CH )

[dlgRes, dummy] = calllib('phfile','PhGetSaveCineName', CH);

end