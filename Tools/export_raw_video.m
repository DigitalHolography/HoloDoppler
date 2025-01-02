function export_raw_video(filename, video)
fd = fopen(filename, 'w+');
fwrite(fd, video(:), 'single');
fclose(fd);
end