function saveGit(output_dirpath)

% SAVING GIT VERSION
% In the txt file in the folder : "log"

filename = 'git_version.txt';

path_file_log = fullfile(output_dirpath, 'log', filename);

gitCommand = 'git status';
[stat, ~] = system(gitCommand);

if stat == 0 % if git is initialised

    gitBranchCommand = 'git symbolic-ref --short HEAD';
    [statusBranch, resultBranch] = system(gitBranchCommand);

    if statusBranch == 0
        resultBranch = strtrim(resultBranch);
        MessBranch = 'Current branch : %s \r';
    else

        vers = readlines('version.txt');
        MessBranch = ['PulseWave GitHub version ', char(vers)];
    end

    gitHashCommand = 'git rev-parse HEAD';
    [statusHash, resultHash] = system(gitHashCommand);

    if statusHash == 0 %hash command was successful
        resultHash = strtrim(resultHash);
        MessHash = 'Latest Commit Hash : %s \r';
    else
        MessHash = '';
    end

    fileID = fopen(path_file_log, 'w');

    fprintf(fileID, '==================\rGIT VERSION :\r');
    fprintf(fileID, MessBranch, resultBranch);
    fprintf(fileID, MessHash, resultHash);
    fprintf(fileID, '==================\r\n ');

    fclose(fileID);

end
end