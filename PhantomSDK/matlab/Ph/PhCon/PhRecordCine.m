function [HRES] = PhRecordCine(CN)

HRES = calllib('phcon','PhRecordCine',CN);
OutputError(HRES);

end

