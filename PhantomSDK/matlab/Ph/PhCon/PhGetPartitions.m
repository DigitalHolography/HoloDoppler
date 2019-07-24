function [HRES,rCount,rPartitionSizes] = PhGetPartitions(CN)

maxCineCnt = PhMaxCineCnt(CN);
pCount=libpointer('uint32Ptr',uint32(maxCineCnt));
psz=zeros(maxCineCnt,1,'uint32');
pPartitionSize=libpointer('uint32Ptr',psz);

[HRES, rCount, rp] = calllib('phcon','PhGetPartitions', CN, pCount, pPartitionSize);
OutputError(HRES);

rPartitionSizes = zeros(rCount,1,'uint32');
for i=1:rCount
    rPartitionSizes(i) = rp(i);
end

end

