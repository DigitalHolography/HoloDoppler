 [txt_name,txt_path] = uigetfile('*.txt');
readlines(fullfile(txt_path,txt_name));

%% launch
HD = HoloDopplerClass;

for ind = 1:length(paths)
    path = paths(ind);
    if ~isfile(path)
        continue
    end
    HD.LoadFile(path); % Load and use the default presets
    % HD.loadParams(path_to_json) % Used to load params
    HD.VideoRendering();
end

%% Show
