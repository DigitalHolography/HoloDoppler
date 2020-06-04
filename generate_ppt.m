function generate_ppt(img_dirname, img_dirpath, fS, f1, f2, output_dir)
import mlreportgen.ppt.*

template_filename = fullfile('resources', 'template.pptx');
PH = fullfile('resources', 'placeholder.png');

split = strsplit(img_dirname,'_');
Date = split{1};
Name = split{2};
Eye = split{3};

IR_A                 = 0.2348;
t_ascend_artery      = 0.0614;
t_mean_artery        = 0.3167;
t_mean_vein          = 0.3375;
t_mean_a2v           = 0.0208;

f                    = [2 6; 2 25; f1 f2];
FrequencyBandLow     = 1;
FrequencyBandHigh    = 1;
FrequencyBand_Movie  = 3;
FrequencyBand_AVG    = 3;
FrequencyBand_Plot   = 3;
FrequencyBand_Resist = 3;

% DataPath_movie       = fullfile(Folder, '200110_GOM0180_OD_ONH1_MOVIE_ff=6_25kHz.gif');
% DataPath_ROIs        = fullfile(Folder, 'ROIs.jpg');
% DataPath_plot        = fullfile(Folder, '200110_GOM0180_OD_ONH1_Plots_ff=6_25kHz.png');
% DataPath_ResMap      = fullfile(Folder, '200110_GOM0180_OD_ONH1_ResMap_ff=6_25kHz.jpg');
% DataPath_systdiast   = fullfile(Folder, '200110_GOM0180_OD_ONH1_SystoleDiastole_ff=6_25kHz.jpg');
% DataPath_composite   = fullfile(Folder, '200110_GOM0180_OD_ONH1_Composite_ff=2_6-6_25kHz.jpg');
% DataPath_movie_cmp   = fullfile(Folder, '200110_GOM0180_OD_ONH1_CompositeMOVIE_ff=2_6-6_25kHz.gif');


slides = Presentation(output_dir, template_filename);
masters = getMasterNames(slides);
% slide_current = add(slides, 'LDH Slide');
slide_current = slides.Children(1);

% Information about patient
contents           = find(slide_current, 'Infos');
chr                = num2str(Date);
chr                = [chr newline Name];
chr                = [chr newline Eye];
replace(contents(1), chr);

% Pulsatile information
% contents           = find(slide_current, 'InfoPulsatility');
% chr                = [sprintf('%.2f', IR_A)];
% chr                = [chr newline sprintf('%.2f', t_ascend_artery) ' s'];
% chr                = [chr newline sprintf('%.2f', t_mean_artery) ' s'];
% chr                = [chr newline sprintf('%.2f', t_mean_vein) ' s'];
% chr                = [chr newline sprintf('%.2f', t_mean_a2v) ' s'];
% replace(contents(1), chr);

% Other infos on measurements
% contents           = find(slide_current, 'InfoMeasurements');
% chr                = [num2str(fS) ' kHz'];
% chr                = [chr newline num2str(f(FrequencyBandLow, 1)) '-' num2str(f(FrequencyBandLow, 2)) ' kHz'];
% chr                = [chr newline num2str(f(FrequencyBandHigh, 1)) '-' num2str(f(FrequencyBandHigh, 2)) ' kHz'];
% replace(contents(1), chr);

picture_size       = '7.7';
%% LIGNE DU HAUT
contents           = find(slide_current, 'PowerDopplerMovie');
f_string           = [num2str(f(FrequencyBand_Movie, 1)) '-' num2str(f(FrequencyBand_Movie, 2)) ' kHz'];
chr                = ['Power Doppler movie, ' f_string];
replace(contents(1), chr);
plane              = Picture(PH);
plane.X            = '5.5cm';
plane.Y            = '1.1cm';
plane.Width        = [picture_size 'cm'];
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);

contents           = find(slide_current, 'PowerDoppler');
f_string           = [num2str(f(FrequencyBand_AVG, 1)) '-' num2str(f(FrequencyBand_AVG, 2)) ' kHz'];
chr                = ['Power Doppler, ' f_string];
replace(contents(1), chr);
img = sprintf('%s_%s.%s', img_dirname, 'DopplerAVG', 'png');
img = sprintf('%s\\png\\%s', img_dirpath, img);
plane              = Picture(img);
plane.X            = '13.62cm';
plane.Y            = '1.1cm';
plane.Width        = [picture_size 'cm'];
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);

contents           = find(slide_current, 'PowerDopplerVariations');
f_string           = [num2str(f(FrequencyBand_Plot, 1)) '-' num2str(f(FrequencyBand_Plot, 2)) ' kHz'];
chr                = ['Power Doppler variations, ' f_string];
replace(contents(1), chr);
plane              = Picture(PH);
plane.X            = '21.57cm';
plane.Y            = '1.1cm';
plane.Width        = '12.3cm';
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);


% LIGNE DU BAS
contents           = find(slide_current, 'ResistivityMap');
f_string           = [num2str(f(FrequencyBand_Resist, 1)) '-' num2str(f(FrequencyBand_Resist, 2)) ' kHz'];
chr                = ['Resistivity, ' f_string];
replace(contents(1), chr);
plane              = Picture(PH);
plane.X            = '0.15cm';
plane.Y            = '11cm';
plane.Width        = ['9.31cm'];
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);

img = sprintf('%s_%s.%s', img_dirname, 'Fmean', 'png');
img = sprintf('%s\\png\\%s', img_dirpath, img);
plane              = Picture(img);
plane.X            = '9.83cm';
plane.Y            = '11cm';
plane.Width        = [picture_size 'cm'];
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);

img = sprintf('%s_%s.%s', img_dirname, 'Color', 'png');
img = sprintf('%s\\png\\%s', img_dirpath, img);
plane              = Picture(img);
plane.X            = '18.02cm';
plane.Y            = '11cm';
plane.Width        = [picture_size 'cm'];
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);

contents           = find(slide_current, 'CompositeMovie');
chr                = 'Composite movie';
replace(contents(1), chr);
plane              = Picture(PH);
plane.X            = '26.03cm';
plane.Y            = '11cm';
plane.Width        = [picture_size 'cm'];
plane.Height       = [picture_size 'cm'];
add(slide_current, plane);

close(slides);
end