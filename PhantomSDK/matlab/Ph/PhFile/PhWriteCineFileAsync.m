function [ HRES ] = PhWriteCineFileAsync( CH )

% function pointer not available, passing NULL
[HRES, dummyAll] = calllib('phfile', 'PhWriteCineFileAsync', CH, libpointer);
OutputError(HRES);

end

