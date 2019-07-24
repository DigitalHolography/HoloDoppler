function [ HRES ] = PhDestroyCine( CH )

[HRES dummyCH] = calllib('phfile','PhDestroyCine',CH);
OutputError(HRES);

end

