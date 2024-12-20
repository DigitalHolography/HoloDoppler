classdef ToolBoxClass < handle

    % Holds useful variables calculated ones and used in the rest of the
    % script

    properties
        %Path of the PW dir and the output dir inside
        Holo_path char
        Holo_name char
        HD_name char
        HD_path char
        HD_path_png char
        HD_path_txt char
        HD_path_avi char
        HD_path_mp4 char
        HD_path_log char
        HD_path_mat char
    end

    methods

        function obj = ToolBoxClass(app)

            obj.Holo_path = app.filepath;
            obj.Holo_name = app.filename;

            [filepath, filename, file_ext] = fileparts(obj.Holo_name);

            dir_name_stem = strrep(filename, file_ext, '');
            list_dir = dir(filepath);
            idx = 0;
            for ii = 1:length(list_dir)
                if contains(list_dir(ii).name, dir_name_stem)
                    match = regexp(list_dir(ii).name, '\d+$', 'match');
                    if ~isempty(match) && str2double(match{1}) >= idx
                        idx = str2double(match{1}) + 1; %suffix
                    end
                end
            end

            if idx == 0
                suffix = 0;
            else
                found_dir = sprintf('%s_HD_%d', dir_name_stem, idx-1);
                match = regexp(found_dir, '\d+$', 'match');
                suffix = str2double(match{1}) + 1;
            end

            obj.HD_name = sprintf("%s_HD_%d", filename, suffix);
            obj.HD_path = fullfile(obj.Holo_path, obj.HD_name);

            obj.HD_path_png = fullfile(obj.HD_path, 'png');
            obj.HD_path_txt = fullfile(obj.HD_path, 'txt');
            obj.HD_path_avi = fullfile(obj.HD_path, 'avi');
            obj.HD_path_mp4 = fullfile(obj.HD_path, 'mp4');
            obj.HD_path_mat = fullfile(obj.HD_path, 'mat');
            obj.HD_path_log = fullfile(obj.HD_path, 'log');

            mkdir(obj.HD_path);
            mkdir(obj.HD_path_png);
            mkdir(obj.HD_path_txt);
            mkdir(obj.HD_path_avi);
            mkdir(obj.HD_path_mp4);
            mkdir(obj.HD_path_mat);
            mkdir(obj.HD_path_log);

            % Turn On Diary Logging
            diary off
            % first turn off diary, so as not to log this script
            diary_filename = fullfile(obj.HD_path_log, sprintf('%s_log.txt', obj.HD_name));
            % setup temp variable with filename + timestamp, echo off
            set(0, 'DiaryFile', diary_filename)
            % set the objectproperty DiaryFile of hObject 0 to the temp variable filename
            clear diary_filename
            % clean up temp variable
            diary on
            % turn on diary logging
            fprintf("==========================================\n")
            fprintf("Current Folder Path: %s\n", obj.Holo_path)
            fprintf("Current File: %s\n", obj.Holo_name)
            fprintf("Start Computer Time: %s\n", datetime('now', 'Format', 'yyyy/MM/dd HH:mm:ss'))
            fprintf("==========================================\n")

            saveGit(obj.HD_path)
        end

    end

end
