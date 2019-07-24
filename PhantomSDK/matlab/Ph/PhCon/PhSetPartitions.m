function [ HRES ] = PhSetPartitions( CN, count, weights )

[HRES, rw] = calllib('phcon','PhSetPartitions', CN, count, weights);
OutputError(HRES);

end

