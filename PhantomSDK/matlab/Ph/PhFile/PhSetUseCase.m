function [ HRES ] = PhSetUseCase( hC, CineUseCaseID )

[HRES, dummy] = calllib('phfile','PhSetUseCase', hC, CineUseCaseID);
OutputError(HRES);

end

