"""Bracketed list overrides share conversion across all dynamic CLI options."""
import pytest

from holodoppler.cli.command import _apply_cli_overrides
from holodoppler.cli.parser import _convert_dynamic_value, parse_args
from holodoppler.config import validate_main_parameters
from test_default_pipeline_contract import parameters


@pytest.mark.parametrize("text,expected", [
    ("[10,10]", [10, 10]),
    ("[0,20,]", [0, 20]),
    (" [1, -2, 3.5, 1e-6,] ", [1, -2, 3.5, 1e-6]),
    ("[]", []),
    ("[1]", [1]),
    ("[[0,200], [200,400],]", [[0, 200], [200, 400]]),
    ('["h5", "png", "a,b"]', ["h5", "png", "a,b"]),
    ("['true', 'null', '10']", ["true", "null", "10"]),
    ("[true, FALSE, null, None, True,]", [True, False, None, None, True]),
    ("[true, null, 1e-6,]", [True, None, 1e-6]),
    ("[[1, 2], [false, 'null'], []]", [[1, 2], [False, "null"], []]),
    ("false", False), ("NULL", None), ("-10", -10), (".25", .25),
    ("Fresnel", "Fresnel"), ("file[1,2].holo", "file[1,2].holo"),
    ("[1,", "[1,"), ("[1,,2]", "[1,,2]"),
    ("[unknown]", "[unknown]"), ("[1+2]", "[1+2]"),
    ("[__import__('os').getcwd()]", "[__import__('os').getcwd()]"),
])
def test_dynamic_value_conversion(text, expected):
    actual = _convert_dynamic_value(text)
    assert actual == expected
    assert type(actual) is type(expected)


@pytest.mark.parametrize("command", ["process", "preview"])
@pytest.mark.parametrize("equals", [False, True])
def test_list_overrides_reach_pipeline_configuration(command, equals):
    options = {"zero_padding": "[10,10]", "pixel_pitch": "[1e-6, 2e-6,]",
               "frequency_bands": "[[0,200],[200,400]]"}
    argv = [command, "README.md", "parameters/default_parameters_default.yaml"]
    for key, value in options.items():
        argv.extend([f"--{key}={value}"] if equals else [f"--{key}", value])
    argv.extend(["--debug", "--svd_threshold=2", "--filter2d=false"])
    args = parse_args(argv)
    original = parameters()
    result = _apply_cli_overrides(original, args)
    assert result["zero_padding"] == [10, 10]
    assert result["pixel_pitch"] == [1e-6, 2e-6]
    assert result["frequency_bands"] == [[0, 200], [200, 400]]
    assert result["svd_threshold"] == 2
    assert result["filter2d"] is False
    assert result["debug"] is True
    assert original["zero_padding"] is False
    validate_main_parameters(result)


@pytest.mark.parametrize("value", ["[-1,10]", "[1.5,10]", "[true,10]"])
def test_list_elements_retain_types_for_parameter_validation(value):
    args = parse_args(["process", "README.md", f"--zero_padding={value}"])
    with pytest.raises((TypeError, ValueError), match="zero_padding"):
        validate_main_parameters(_apply_cli_overrides(parameters(), args))


@pytest.mark.parametrize("command", ["process", "preview"])
def test_list_override_with_default_config(command):
    args = parse_args([command, "README.md", "--zero_padding=[10, 10,]"])
    assert args.config is None
    assert args.dynamic_options == {"zero_padding": [10, 10]}
