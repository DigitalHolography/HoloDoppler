function [HRES, ramCnt, flashCnt] = PhGetCineCount(CN)

[HRES, ramCnt, flashCnt] = calllib('phcon','PhGetCineCount',CN,0,0);
OutputError(HRES);

end

