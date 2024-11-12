function varOut = loadGUIVariable(varIn)
try
    varOut = varIn;
catch ME
    fprintf("==============================\nERROR\n==============================\n")
    disp('Error Message:')
    disp(ME.message)
    for i = 1:numel(ME.stack)
        fprintf('%s : %s, line : %d \n',ME.stack(i).file, ME.stack(i).name, ME.stack(i).line);
    end
end
end