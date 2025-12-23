% Clean up previous build folder to avoid conflicts
if isfolder('build')

    try
        rmdir('build', 's');
        fprintf('Removed existing build directory.\n');
    catch ME
        warning('Could not remove build directory. Is a file open?');
    end

end

mkdir('build');

% Prepare Paths for Compilation
% Add all source folders to the MATLAB path so the compiler can find dependencies
addpath('AberrationCorrection');
addpath('FolderManagement');
addpath('Imaging');
addpath('Interface');
addpath('ReaderClasses');
addpath('Rendering');
addpath('Saving');
addpath('Scripts');
addpath('StandardConfigs');
addpath('Tools');

% Configure Build Options
buildOpts = compiler.build.StandaloneApplicationOptions('holodopplercli.m');
buildOpts.ExecutableName = 'holodoppler';
buildOpts.OutputDir = 'build';
buildOpts.Verbose = 'on';
buildOpts.TreatInputsAsNumeric = 'off';

% --- SET ICON HERE ---
if isfile('holoDopplerLogo.png')
    buildOpts.ExecutableIcon = 'holoDopplerLogo.png';
else
    warning('Logo file not found. Executable will have default icon.');
end

% --- ADD ASSETS ---
buildOpts.AdditionalFiles = [
                             "version.txt", ...
                                 "StandardConfigs\Phantom S711 37kHz retinal analysis.json", ...
                                 "StandardConfigs\CurrentDefault.txt"
                             ];

% Run Compilation
results = compiler.build.standaloneApplication(buildOpts);
