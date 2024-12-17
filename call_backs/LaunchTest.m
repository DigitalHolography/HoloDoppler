paths = readlines("C:\Users\Vladikavkaz\Documents\data_holo_test_list.txt");

%% launch

for ind = 1:length(paths)
    path = paths(ind);
    [filepath,filename,ext] = fileparts(path);
    cache = [];
    %cache = fetch_cache(filepath,filename,ext);
    RenderFile(path,cache);
end


