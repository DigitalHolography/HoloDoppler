function classtogui(HD, app)
% classtogui  Push all HD.params values into the app UI.
%
% Driven entirely by HDParamSchema — add a parameter there, not here.

if isempty(HD) || isempty(HD.params)
    return
end

schema = HDParamSchema();

for k = 1:numel(schema)
    e = schema(k);

    % Skip entries whose widget doesn't exist on this app
    if ~widgetExists(app, e.widget)
        continue
    end

    % Read param value (fall back to schema default if absent)
    value = getParam(HD.params, e.param, e.default);

    switch e.type
        case 'numeric'
            setNumeric(app.(e.widget), value);

        case 'checkbox'
            setCheckbox(app.(e.widget), value);

        case 'dropdown'
            setDropdown(app.(e.widget), value);

        case 'range2'
            % e.param is the HD field (1x2 vector); e.widget is a 2-element cell
            if numel(value) >= 2
                setNumeric(app.(e.widget{1}), value(1));
                setNumeric(app.(e.widget{2}), value(2));
            end

        case 'listbox'
            setListbox(app.(e.widget), value);
    end

end

% ---- things that need special logic beyond the schema -------------------

% Image dimensions come from HD.file, not HD.params
if ~isempty(HD.file)
    setNumeric(app.Nx, double(HD.file.Nx));
    setNumeric(app.Ny, double(HD.file.Ny));

    if isfield(HD.file, 'num_frames')

        try
            app.positioninfileSlider.Limits = double([1 HD.file.num_frames]);
            setNumeric(app.positioninfileSlider, double(HD.params.framePosition));
        catch
        end

    end

end

end

% ===========================================================================
% Private helpers
% ===========================================================================

function tf = widgetExists(app, widget)
% True when the widget name is a non-empty string and app has that property.
if isempty(widget) || (iscell(widget) && any(cellfun(@isempty, widget)))
    tf = false;
    return
end

if iscell(widget)
    tf = all(cellfun(@(w) isprop(app, w), widget));
else
    tf = isprop(app, widget);
end

end

function value = getParam(params, name, default)
% Return params.(name) if it exists and is non-empty, otherwise default.
if isfield(params, name) && ~isempty(params.(name))
    value = params.(name);
else
    value = default;
end

end

function setNumeric(field, value)

if isempty(value) || ~isnumeric(value)
    value = 0;
end

try
    field.Value = double(value(1));
catch ME
    warning('classtogui:setNumeric', 'Could not set numeric field: %s', ME.message);
end

end

function setCheckbox(field, value)

if isempty(value)
    value = false;
end

try
    field.Value = logical(value);
catch ME
    warning('classtogui:setCheckbox', 'Could not set checkbox: %s', ME.message);
end

end

function setDropdown(field, value)

if isempty(value)
    value = field.Items{1};
end

try

    if ismember(value, field.Items)
        field.Value = value;
    else
        warning('classtogui:setDropdown', ...
            'Value "%s" not in dropdown items — keeping current value.', value);
    end

catch ME
    warning('classtogui:setDropdown', 'Could not set dropdown: %s', ME.message);
end

end

function setListbox(field, value)
% Populate Items from ImageTypeList then select the active ones.
try
    allTypes = properties(ImageTypeList);
catch
    allTypes = {'power_Doppler', 'color_Doppler', 'directional_Doppler', ...
                    'moment_0', 'moment_1', 'moment_2', 'FH_modulus_mean'};
end

field.Items = allTypes;

if ~isempty(value)
    field.Value = intersect(value, allTypes, 'stable');
else
    field.Value = {};
end

end
