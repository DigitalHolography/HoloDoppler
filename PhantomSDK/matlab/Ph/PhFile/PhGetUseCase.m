function [ HRES cineUseCaseID] = PhGetUseCase( hC )

pCineUseCaseID = libpointer('int32Ptr',0);
[HRES, dummyAll] = calllib('phfile','PhGetUseCase', hC, pCineUseCaseID);
cineUseCaseID = pCineUseCaseID.Value;
OutputError(HRES);

end

