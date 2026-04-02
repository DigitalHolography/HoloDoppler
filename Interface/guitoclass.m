function guitoclass(HD, app)
% guitoclass  Push all app UI values into HD.params.
%
% Driven entirely by HDParamSchema — add a parameter there, not here.

if isempty(HD)
    return
end

schema = HDParamSchema();

for k = 1:numel(schema)
    e = schema(k);

    % Skip entries whose widget doesn't exist on this app
    if ~widgetExists(app, e.widget)
        continue
    end

    switch e.type
        case 'numeric'
            HD.params.(e.param) = getNumeric(app.(e.widget), e.default);

        case 'checkbox'
            HD.params.(e.param) = getCheckbox(app.(e.widget), e.default);

        case 'dropdown'
            HD.params.(e.param) = getDropdown(app.(e.widget), e.default);

        case 'listbox'
            HD.params.(e.param) = getListbox(app.(e.widget), e.default);
    end

end

% ---- framePosition: driven by slider (the canonical position source) ------
if isprop(app, 'positioninfileSlider')
    HD.params.framePosition = round(app.positioninfileSlider.Value);
end

end

% ===========================================================================
% Private helpers
% ===========================================================================

function tf = widgetExists(app, widget)

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

function val = getNumeric(field, default)

try
    val = double(field.Value);

    if isempty(val) || ~isfinite(val)
        val = default;
    end

catch
    val = default;
end

end

function val = getCheckbox(field, default)

try
    val = logical(field.Value);
catch
    val = default;
end

end

function val = getDropdown(field, default)

try
    val = field.Value;

    if isempty(val)
        val = default;
    end

catch
    val = default;
end

end

function val = getListbox(field, default)

try
    val = field.Value;

    if isempty(val)
        val = default;
    end

catch
    val = default;
end

end
