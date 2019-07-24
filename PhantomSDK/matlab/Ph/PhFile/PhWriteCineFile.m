function [ HRES ] = PhWriteCineFile( CH )

% function pointer not available, passing NULL
[HRES, dummyAll] = calllib('phfile', 'PhWriteCineFile', CH, libpointer);
OutputError(HRES);

end

