function FolderManagement(app)
% This function creates a dialog for managing folders and files for rendering.

% Calculate initial height
initialHeight = 130 + length(app.HD.drawer_list) * 14;

d = uifigure('Position', [300, 300, 750, initialHeight], ...
    'Color', [0.2, 0.2, 0.2], ...
    'Name', 'Folder management', ...
    'Resize', 'on', ...
    'WindowStyle', 'modal'); % 'modal' makes it behave like a dialog

% Create main grid layout (2 rows, 1 column)
mainGrid = uigridlayout(d, [2, 1], ...
    'ColumnWidth', {'1x'}, ...
    'RowHeight', {'1x', 'fit'}, ...
    'Padding', [10, 10, 10, 10], ...
    'BackgroundColor', [0.2, 0.2, 0.2]);

% Create the text area for displaying the list
% Convert drawer_list to cell array of strings if it's empty
if isempty(app.HD.drawer_list)
    displayValue = {''};
else
    displayValue = app.HD.drawer_list;
end

% Create the text area for displaying the list
txt = uitextarea('Parent', mainGrid, ...
    'BackgroundColor', [0.2, 0.2, 0.2], ...
    'FontColor', [0.8, 0.8, 0.8], ...
    'Position', [20, 90, 710, length(app.HD.drawer_list) * 14], ...
    'Value', displayValue, ...
    'Editable', 'off');
txt.Layout.Row = 1;
txt.Layout.Column = 1;

% Button grid (2 rows, 6 columns)
buttonGrid = uigridlayout(mainGrid, [2, 6], ...
    'ColumnWidth', repmat({'1x'}, 1, 6), ...
    'RowHeight', {'1x', '1x'}, ...
    'Padding', [5, 5, 5, 5], ...
    'BackgroundColor', [0.2, 0.2, 0.2]);
buttonGrid.Layout.Row = 2;
buttonGrid.Layout.Column = 1;

% Create checkbox
keep_z_distance = uicheckbox('Parent', buttonGrid, ...
    'Position', [500, 50, 120, 25], ...
    'FontColor', [0.9 0.9 0.9], ...
    'Text', 'Keep z distance', ...
    'Value', 0);
keep_z_distance.Layout.Row = 2;
keep_z_distance.Layout.Column = 5;

% Create buttons using uibutton
makeDrawerButton(buttonGrid, [1, 1], 'Select file', ...
    @(~, ~) drawerSelectFile(app, d, txt));
makeDrawerButton(buttonGrid, [2, 1], 'Select Current', ...
    @(~, ~) drawerSelectCurrent(app, d, txt));
makeDrawerButton(buttonGrid, [2, 2], 'Select Current Folder', ...
    @(~, ~) drawerSelectCurrentFolder(app, d, txt));
makeDrawerButton(buttonGrid, [1, 2], 'Select folder', ...
    @(~, ~) drawerSelectFolder(app, d, txt));
makeDrawerButton(buttonGrid, [1, 3], 'Clear list', ...
    @(~, ~) drawerClearList(app, d, txt));
makeDrawerButton(buttonGrid, [1, 4], 'Save configs', ...
    @(~, ~) drawerSaveConfigs(app, keep_z_distance));
makeDrawerButton(buttonGrid, [2, 4], 'Delete all configs', ...
    @(~, ~) drawerDeleteConfigs(app));
makeDrawerButton(buttonGrid, [1, 5], 'Render', ...
    @(~, ~) drawerRender(app));
makeDrawerButton(buttonGrid, [1, 6], 'Save to txt', ...
    @(~, ~) drawerSaveTxt(app));
makeDrawerButton(buttonGrid, [2, 6], 'Load from txt', ...
    @(~, ~) drawerLoadTxt(app, d, txt));

end

function makeDrawerButton(parent, pos, label, cb)
Button = uibutton(parent, 'push', ...
    'BackgroundColor', [0.5, 0.5, 0.5], ...
    'FontColor', [0.9, 0.9, 0.9], ...
    'Text', label, ...
    'ButtonPushedFcn', cb);
Button.Layout.Row = pos(1);
Button.Layout.Column = pos(2);
end

function updateDrawerDisplay(app, d, txt)
% Convert drawer_list to cell array of strings if it's empty
if isempty(app.HD.drawer_list)
    displayValue = {''};
else
    displayValue = app.HD.drawer_list;
end

% Update the text area with the current list
txt.Value = displayValue;

% Resize the window and text area
newHeight = 100 + length(app.HD.drawer_list) * 14;
if newHeight > d.Position(4)
    d.Position(4) = newHeight;
end

end

function drawerSelectFile(app, d, txt)

if ~isempty(app.HD.drawer_list)
    [selected_file, path] = uigetfile(app.HD.drawer_list{end}, 'Select File', '*.holo;*.cine');
else
    [selected_file, path] = uigetfile('Select File', '*.holo;*.cine');
end

if selected_file
    [~, ~, ext] = fileparts(selected_file);

    if ismember(ext, {'.cine', '.holo'})
        app.HD.drawer_list{end + 1} = fullfile(path, selected_file);
    else
        uialert(d, 'File should be of extension .cine or .holo', 'Invalid File Type');
    end

else
    return;

end

updateDrawerDisplay(app, d, txt);
end

function drawerSelectCurrent(app, d, txt)

if isempty(app.HD.file)
    uialert(d, 'No current file loaded', 'No File');
    return;
end

selected_file = app.HD.file.path;
[~, ~, ext] = fileparts(selected_file);

if ismember(ext, {'.cine', '.holo'})
    app.HD.drawer_list{end + 1} = selected_file;
else
    uialert(d, 'File should be of extension .cine or .holo', 'Invalid File Type');
end

updateDrawerDisplay(app, d, txt);
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

updateDrawerDisplay(app, d, txt);
end

function drawerSelectCurrentFolder(app, d, txt)

if isempty(app.HD.file)
    uialert(d, 'No current file loaded', 'No File');
    return;
end

drawerAddFilesFromFolder(app, app.HD.file.dir, d, txt);
end

function drawerSelectFolder(app, d, txt)

if ~isempty(app.HD.drawer_list)
    [last_folder, ~, ~] = fileparts(app.HD.drawer_list{end});
else
    last_folder = [];
end

selected_folder = uigetdir(last_folder);

if selected_folder
    drawerAddFilesFromFolder(app, selected_folder, d, txt);
end

end

function drawerClearList(app, d, txt)
app.HD.drawer_list = {};
updateDrawerDisplay(app, d, txt);
end

function drawerLoadTxt(app, d, txt)
[selected_file, path] = uigetfile('*.txt', 'Select File');

if selected_file == 0
    return;
end

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

updateDrawerDisplay(app, d, txt);
end

function drawerSaveTxt(app)
[selected_file, path] = uigetfile('*.txt', 'Select File');

if selected_file == 0
    return;
end

writelines(app.HD.drawer_list, fullfile(path, selected_file));
end

function drawerSaveConfigs(app, keepZControl)

for i = 1:length(app.HD.drawer_list)
    app.HD.saveParams(app.HD.drawer_list{i}, keepZControl.Value);
end

% Optional: Show confirmation
% uialert(d, 'Configurations saved successfully', 'Success');
end

function drawerRender(app)
fileList = buildDrawerFileList(app);

for i = 1:length(fileList)
    entry = fileList{i};

    if ~isempty(entry) && ~isempty(entry{2})

        for j = 1:length(entry{2})
            app.HD.LoadFile(entry{1}, params = entry{2}{j});
            app.HD.VideoRendering();
        end

    end

end

end

function drawerDeleteConfigs(app)
fileList = buildDrawerFileList(app);

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
