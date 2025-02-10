function highest_number = get_highest_number_in_directories(directory, search_str)
    % Initialize the highest number to be 0 (so it can be updated)
    highest_number = 0;
    
    % List all files and folders in the current directory
    files = dir(directory);
    
    % Loop through all the files and folders
    for i = 1:numel(files)
        % Get the current file or folder's name
        file_name = files(i).name;
        % Skip '.' and '..' directories
        if strcmp(file_name, '.') || strcmp(file_name, '..')
            continue;
        end
        % Check if the current item is a directory (subdirectory)
        if files(i).isdir
            % Check if the file name contains the search string
            if contains(file_name, search_str)
                % Use a regular expression to find numbers at the end of the file name
                tokens = regexp(file_name, '(\d+)$', 'tokens');
                
                % If a number is found at the end of the file name
                if ~isempty(tokens)
                    % Extract the number (from the first token in the cell array)
                    num = str2double(tokens{1}{1});
                    
                    % Update the highest number if the current number is higher
                    highest_number = max(highest_number, num);
                end
            end
        end
    end
    
    % If no valid number is found, return a message or default value (e.g., 0)
    if highest_number == 0
        %disp('No files with the specified string and a number at the end were found.');
    end
end
