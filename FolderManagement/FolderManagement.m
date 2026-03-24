function FolderManagement(app)
% This function creates a dialog for managing folders and files for rendering.

d = dialog('Position', [300, 300, 750, 130 + length(app.HD.drawer_list) * 14], ...
    'Color', [0.2, 0.2, 0.2], ...
    'Name', 'Folder management', ...
    'Resize', 'on', ...
    'WindowStyle', 'normal');

txt = uicontrol('Parent', d, ...
    'Style', 'text', ...
    'FontName', 'Helvetica', ...
    'BackgroundColor', [0.2, 0.2, 0.2], ...
    'ForegroundColor', [0.8, 0.8, 0.8], ...
    'Position', [20, 90, 710, length(app.HD.drawer_list) * 14], ...
    'HorizontalAlignment', 'left', ...
    'String', app.HD.drawer_list);

keep_z_distance = uicontrol('Parent', d, ...
    'Style', 'checkbox', ...
    'Position', [500, 50, 100, 25], ...
    'FontName', 'Helvetica', ...
    'BackgroundColor', [0.5, 0.5, 0.5], ...
    'FontWeight', 'bold', ...
    'String', 'Keep z distance', ...
    'Value', 0);

makeDrawerButton(d, [20, 20], 'Select file', @(~, ~) drawerSelectFile(d, txt));
makeDrawerButton(d, [20, 50], 'Select Current', @(~, ~) drawerSelectCurrent(d, txt));
makeDrawerButton(d, [140, 50], 'Select Current Folder', @(~, ~) drawerSelectCurrentFolder(d, txt));
makeDrawerButton(d, [140, 20], 'Select folder', @(~, ~) drawerSelectFolder(d, txt));
makeDrawerButton(d, [260, 20], 'Clear list', @(~, ~) drawerClearList(d, txt));
makeDrawerButton(d, [380, 20], 'Save configs', @(~, ~) drawerSaveConfigs(keep_z_distance));
makeDrawerButton(d, [380, 50], 'Delete all configs', @(~, ~) drawerDeleteConfigs());
makeDrawerButton(d, [500, 20], 'Render', @(~, ~) drawerRender());
makeDrawerButton(d, [620, 20], 'Save to txt', @(~, ~) drawerSaveTxt());
makeDrawerButton(d, [620, 50], 'Load from txt', @(~, ~) drawerLoadTxt(d, txt));

end

function makeDrawerButton(~, parent, pos, label, cb)
uicontrol('Parent', parent, ...
    'Position', [pos, 100, 25], ...
    'FontName', 'Helvetica', ...
    'BackgroundColor', [0.5, 0.5, 0.5], ...
    'ForegroundColor', [0.9 0.9 0.9], ...
    'FontWeight', 'bold', ...
    'String', label, ...
    'Callback', cb);
end

function updateDrawerDisplay(app, d, txt)
txt.String = app.HD.drawer_list;
d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
txt.Position(4) = length(app.HD.drawer_list) * 14;
end

function drawerSelectFile(app, d, txt)

if ~isempty(app.HD.drawer_list)
    [selected_file, path] = uigetfile(app.HD.drawer_list{end}, 'Select File');
else
    [selected_file, path] = uigetfile('Select File');
end

if selected_file
    [~, ~, ext] = fileparts(selected_file);

    if ismember(ext, {'.cine', '.holo'})
        app.HD.drawer_list{end + 1} = fullfile(path, selected_file);
    else
        fprintf("File should be of extension .cine or .holo\n");
    end

end

updateDrawerDisplay(d, txt);
end

function drawerSelectCurrent(app, d, txt)

if isempty(app.HD.file)
    return
end

selected_file = app.HD.file.path;
[~, ~, ext] = fileparts(selected_file);

if ismember(ext, {'.cine', '.holo'})
    app.HD.drawer_list{end + 1} = selected_file;
else
    fprintf("File should be of extension .cine or .holo\n");
end

updateDrawerDisplay(d, txt);
end

function drawerAddFilesFromFolder(app, folder, d, txt)
entries = dir(folder);

for i = 1:numel(entries)

    if ~entries(i).isdir
        [~, ~, ext] = fileparts(entries(i).name);

        if ismember(ext, {'.cine', '.holo'})
            app.HD.drawer_list{end + 1} = fullfile(folder, entries(i).name);
        end

    end

end

updateDrawerDisplay(d, txt);
end

function drawerSelectCurrentFolder(app, d, txt)

if isempty(app.HD.file)
    return
end

drawerAddFilesFromFolder(app.HD.file.dir, d, txt);
end

function drawerSelectFolder(app, d, txt)

if ~isempty(app.HD.drawer_list)
    [last_folder, ~, ~] = fileparts(app.HD.drawer_list{end});
else
    last_folder = [];
end

selected_folder = uigetdir(last_folder);

if selected_folder
    drawerAddFilesFromFolder(selected_folder, d, txt);
end

end

function drawerClearList(app, d, txt)
app.HD.drawer_list = {};
updateDrawerDisplay(d, txt);
end

function drawerLoadTxt(app, d, txt)
[selected_file, path] = uigetfile('*.txt', 'Select File');
lines = readlines(fullfile(path, selected_file));

for i = 1:numel(lines)

    if ~isempty(lines(i))

        try
            [~, ~, ext] = fileparts(lines(i));

            if ismember(ext, {'.cine', '.holo'})
                app.HD.drawer_list{end + 1} = lines(i);
            end

        catch e
            disp(e)
        end

    end

end

updateDrawerDisplay(d, txt);
end

function drawerSaveTxt(app)
[selected_file, path] = uigetfile('*.txt', 'Select File');
writelines(app.HD.drawer_list, fullfile(path, selected_file));
end

function drawerSaveConfigs(app, keepZControl)

for i = 1:length(app.HD.drawer_list)
    app.HD.saveParams(app.HD.drawer_list{i}, keepZControl.Value);
end

end

function drawerRender(app)
fileList = buildDrawerFileList();

for i = 1:length(fileList)
    entry = fileList{i};

    if ~isempty(entry)
        configs = entry{2};

        for j = 1:length(configs)
            app.HD.LoadFile(entry{1}, params = configs{j});
            app.HD.VideoRendering();
        end

    end

end

end

function drawerDeleteConfigs()
fileList = buildDrawerFileList();

for i = 1:length(fileList)
    entry = fileList{i};

    if ~isempty(entry) && ~isempty(entry{2})

        for j = 1:length(entry{2})
            delete(entry{2}{j});
        end

    end

end

end

function fileList = buildDrawerFileList(app)
fileList = cell(size(app.HD.drawer_list));

for i = 1:length(app.HD.drawer_list)
    config_list = get_config_files(app.HD.drawer_list{i});

    if ~isempty(config_list)
        fileList{i} = {app.HD.drawer_list{i}, config_list};
    end

end

end
