function save_string_cells_to_file(filename, infos)
% save a string cell array to a file, inserting a new line between each
% cell (this is used to store patient informations to a text file)
fd = fopen(filename, "wt+");
for n = 1:numel(infos)
    fprintf(fd, "%s\n", infos{n});
end
fclose(fd);
end