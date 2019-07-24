function [ HRES ] = PhSetCineParams( CN, cinePartNo, acquisitionParams )

acqParams = libstruct('tagACQUIPARAMS', acquisitionParams);
[HRES, dummy] = calllib('phcon', 'PhSetCineParams', CN, cinePartNo, acqParams);
OutputError(HRES);

end

