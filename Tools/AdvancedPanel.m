function AdvancedPanel(app)
% Create the UIFigure with improved styling
fig = uifigure('Name', 'Advanced Controls', ...
    'Position', [100 100 450 250], ...
    'Color', [0.2 0.2 0.2], ...
    'Resize', 'off');

% Create a grid layout for better organization
gl = uigridlayout(fig);
gl.RowHeight = {'fit', 'fit', 'fit', 'fit', 'fit', 'fit'}; % 6 rows
gl.ColumnWidth = {150, 150, 150}; % 3 columns
gl.BackgroundColor = [0.2 0.2 0.2];
gl.Padding = [10 10 10 10];
gl.RowSpacing = 10;
gl.ColumnSpacing = 10;

% Style constants
bgColor = [0.25 0.25 0.25];
textColor = [0.9 0.9 0.9];
btnColor = [0.4 0.4 0.4];

% Frame position controls - Row 1
label1 = uilabel(gl);
label1.Text = 'First frame position:';
label1.FontColor = textColor;
label1.BackgroundColor = bgColor;
label1.Layout.Row = 1;
label1.Layout.Column = 1;

firstFrameEdit = uieditfield(gl, 'numeric');
firstFrameEdit.Value = app.HD.params.first_frame;
firstFrameEdit.BackgroundColor = bgColor;
firstFrameEdit.FontColor = textColor;
firstFrameEdit.Layout.Row = 2;
firstFrameEdit.Layout.Column = 1;

% Last frame position - Row 1
label2 = uilabel(gl);
label2.Text = 'Last frame position:';
label2.FontColor = textColor;
label2.BackgroundColor = bgColor;
label2.Layout.Row = 1;
label2.Layout.Column = 2;

lastFrameEdit = uieditfield(gl, 'numeric');
lastFrameEdit.Value = app.HD.params.end_frame;
lastFrameEdit.BackgroundColor = bgColor;
lastFrameEdit.FontColor = textColor;
lastFrameEdit.Layout.Row = 2;
lastFrameEdit.Layout.Column = 2;

% Color threshold controls - Row 3
label3 = uilabel(gl);
label3.Text = 'Color frequency threshold:';
label3.FontColor = textColor;
label3.BackgroundColor = bgColor;
label3.Layout.Row = 3;
label3.Layout.Column = 1;

colorThreshEdit = uieditfield(gl, 'numeric');
colorThreshEdit.Value = app.HD.view.LastParams.time_range_extra;
colorThreshEdit.BackgroundColor = bgColor;
colorThreshEdit.FontColor = textColor;
colorThreshEdit.Layout.Row = 4;
colorThreshEdit.Layout.Column = 1;

% Buckets number controls - Row 3
label4 = uilabel(gl);
label4.Text = 'Buckets number:';
label4.FontColor = textColor;
label4.BackgroundColor = bgColor;
label4.Layout.Row = 3;
label4.Layout.Column = 2;

bucketsEdit = uieditfield(gl);
buckranges = app.HD.params.buckets_ranges;
% buckranges(:,2) = round(app.HD.params.fs/2,2); % set to half fs the max range by def
bucketsEdit.Value = mat2str(buckranges);
bucketsEdit.BackgroundColor = bgColor;
bucketsEdit.FontColor = textColor;
bucketsEdit.Layout.Row = 4;
bucketsEdit.Layout.Column = 2;
buckEditCallBack(bucketsEdit);

bucketsraw = uicheckbox(gl, ...
    'Text', 'save raw', ...
    'FontColor', 'white', ...
    'Value', app.HD.params.buckets_raw, ...
    'ValueChangedFcn', @(src, event) updateParam(app, src, 'buckets_raw'));
bucketsraw.Layout.Row = 3;
bucketsraw.Layout.Column = 3;

% Show SH button - Row 5
showSHbtn = uibutton(gl, 'push');
showSHbtn.Text = 'Show SH';
showSHbtn.BackgroundColor = btnColor;
showSHbtn.FontColor = textColor;
showSHbtn.Layout.Row = 5;
showSHbtn.Layout.Column = 1;
showSHbtn.ButtonPushedFcn = @(btn, event) showSH_Callback(app);

% Explore SH button - Row 5
showSHbtn = uibutton(gl, 'push');
showSHbtn.Text = 'Explore SH';
showSHbtn.BackgroundColor = btnColor;
showSHbtn.FontColor = textColor;
showSHbtn.Layout.Row = 5;
showSHbtn.Layout.Column = 2;
showSHbtn.ButtonPushedFcn = @(btn, event) ExploreSH(app);

% Explore SH broadening button  - Row 5
showSHbtn = uibutton(gl, 'push');
showSHbtn.Text = 'Explore SH broadening';
showSHbtn.BackgroundColor = btnColor;
showSHbtn.FontColor = textColor;
showSHbtn.Layout.Row = 5;
showSHbtn.Layout.Column = 3;
showSHbtn.ButtonPushedFcn = @(btn, event) ExploreSHbroadening(app.HD.view.SH, app.HD.file.fs, app.HD.params.time_range(1), app.HD.params.time_range(2));

% Explore Ap button  - Row 6
showSHbtn = uibutton(gl, 'push');
showSHbtn.Text = 'Explore Ap';
showSHbtn.BackgroundColor = btnColor;
showSHbtn.FontColor = textColor;
showSHbtn.Layout.Row = 6;
showSHbtn.Layout.Column = 1;
showSHbtn.ButtonPushedFcn = @(btn, event) ExploreAp(app.HD.view.Frames, app.HD.params);

% Explore Quant - Row 6
showSHbtn = uibutton(gl, 'push');
showSHbtn.Text = 'Explore Quant';
showSHbtn.BackgroundColor = btnColor;
showSHbtn.FontColor = textColor;
showSHbtn.Layout.Row = 6;
showSHbtn.Layout.Column = 2;
showSHbtn.ButtonPushedFcn = @(btn, event) ExploreQuant(app.HD);

% Explore  - Row 6
showSHbtn = uibutton(gl, 'push');
showSHbtn.Text = 'Explore Z';
showSHbtn.BackgroundColor = btnColor;
showSHbtn.FontColor = textColor;
showSHbtn.Layout.Row = 6;
showSHbtn.Layout.Column = 3;
showSHbtn.ButtonPushedFcn = @(btn, event) ExploreZ(app.HD.view, app.HD.params);

% Set up value change callbacks
firstFrameEdit.ValueChangedFcn = @(src, event) updateFrameParams(app, src, lastFrameEdit, 'first');
lastFrameEdit.ValueChangedFcn = @(src, event) updateFrameParams(app, firstFrameEdit, src, 'last');
colorThreshEdit.ValueChangedFcn = @(src, event) updateParam(app, src, 'time_range_extra');

function buckEditCallBack(src)

    try
        app.HD.params.buckets_ranges = eval(src.Value);
        assert(size(app.HD.params.buckets_ranges, 2) == 2);
    catch E
        disp("Couldn't get the ranges try to write input frequency ranges like '[[6,18]; [6,25]]' in kHz.")
        disp(E)
    end

end

bucketsEdit.ValueChangedFcn = @(src, event) buckEditCallBack(src);

% Add validation for frame values
firstFrameEdit.Limits = [0 Inf];
lastFrameEdit.Limits = [0 Inf];
firstFrameEdit.RoundFractionalValues = 'on';
lastFrameEdit.RoundFractionalValues = 'on';

% Callback functions
function showSH_Callback(app)
    app.HD.show_SH();
end

function updateFrameParams(app, edit1, edit2, which)
    % Validate frame order
    if edit1.Value > edit2.Value

        if strcmp(which, 'first')
            edit1.Value = edit2.Value;
        else
            edit2.Value = edit1.Value;
        end

        uialert(app.UIFigure, 'First frame must be ≤ last frame', 'Invalid Frame Order');
    end

    % Update parameters
    app.HD.params.first_frame = edit1.Value;
    app.HD.params.end_frame = edit2.Value;
end

function updateParam(app, src, paramName)
    app.HD.params.(paramName) = src.Value;
end

end
