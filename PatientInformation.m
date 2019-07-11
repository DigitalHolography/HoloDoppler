classdef PatientInformation
properties
    first_name
    last_name
    year_of_birth
    notes
end
methods (Access = public)
    function obj = PatientInformation(first_name, last_name, year_of_birth, notes)
        obj.first_name = first_name;
        obj.last_name = last_name;
        obj.year_of_birth = year_of_birth;
        obj.notes = notes;
    end
    
    function save_to_file(obj, filename)
        fd = fopen(filename, 'wt+');
        fprintf(fd, 'FirstName=%s\nLastName=%s\nYearOfBirth=%d\nNotes:\n%s\n', obj.first_name, obj.last_name, obj.year_of_birth, obj.notes);
        fclose(fd);
    end
    

end
methods (Static)
    function object = read_from_file(filename)
        fd = fopen(filename, 'rt');
        fname = fscanf(fd, 'FirstName=%s\n');
        lname = fscanf(fd, 'LastName=%s\n');
        yob = fscanf(fd, 'YearOfBirth=%d\n');
        fgetl(fd);
        tline=1;
        notes = [];
        while tline ~= -1
            tline = fgetl(fd);
            if tline ~= -1
                notes = sprintf('%s\n%s', notes, tline);
            end
        end
        fclose(fd);
        object = PatientInformation(fname, lname, yob, strtrim(notes));
    end
end
end