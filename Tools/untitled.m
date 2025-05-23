h5path="U:\250110_MAO0581\250110_MAO0581_OS12OD34_1_HD_10\raw\250110_MAO0581_OS12OD34_1_HD_10_raw.h5";
info = h5info(h5path);
data = struct();

for i = 1:numel(info.Datasets)
    data.(info.Datasets(i).Name) = h5read(h5path,strcat("/",info.Datasets(i).Name));
end
[numX,numY,numC,numT] = size(data.(sprintf("Q%d_m1",1)));
for i = 1:4
    fAVG.(sprintf("Q%d",i)) = data.(sprintf("Q%d_m1",i))./mean(data.(sprintf("Q%d_m0",i)),[1 2]);
end
for i = 1:4
    f0.(sprintf("Q%d",i)) = sqrt(data.(sprintf("Q%d_m0",i))./mean(data.(sprintf("Q%d_m0",i)),[1 2]));
end

QuadrantsM1 = mergeColorsVideo({fAVG.Q1,fAVG.Q2,fAVG.Q3,fAVG.Q4});
QuadrantsM0 = mergeColorsVideo({f0.Q1,f0.Q2,f0.Q3,f0.Q4});

QuadrantsDiff = mergeColorsVideo({fAVG.Q1-fAVG.Q3, fAVG.Q2-fAVG.Q4,fAVG.Q1-fAVG.Q3, fAVG.Q2-fAVG.Q4 });