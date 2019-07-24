function [ HRES ] = PhSetSingleCineParams( CN, acquisitionParams )

acqParams = libstruct('tagACQUIPARAMS', acquisitionParams);
[HRES, dummy] = calllib('phcon','PhSetSingleCineParams', CN, acqParams);
OutputError(HRES);

end

