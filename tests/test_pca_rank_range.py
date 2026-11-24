"""Adaptive PCA ranges are parsed as data and resolved independently per packet."""

import numpy as np
import pytest
import yaml

from holodoppler.config.validation import validate_main_parameters
from holodoppler.core.filtering import (
    _resolve_pca_index_range, pca_packet_mean, pca_time_transform,
    validate_pca_index_range,
)
from test_default_pipeline_contract import parameters


def test_requested_yaml_syntax_passes_parameter_validation():
    options = yaml.safe_load('pca_index_range: [0, 0.1*"effective rank"]')
    validate_main_parameters(parameters(**options))
    assert _resolve_pca_index_range(np, options['pca_index_range'], np.ones(32)) == (0, 4)


def test_packet_mean_resolves_rank_per_packet():
    rng = np.random.default_rng(42)
    frames = rng.normal(size=(8, 2, 2)) + 1j * rng.normal(size=(8, 2, 2))
    frames[4:] *= np.array([1, .01, .001, .0001])[:, None, None]
    images, ends = [], []
    for packet in (frames[:4], frames[4:]):
        matrix = packet.reshape(4, -1).T
        values, vectors = np.linalg.eigh(matrix.conj().T @ matrix)
        p = np.maximum(values, 0) / np.maximum(values, 0).sum()
        rank = np.exp(-np.sum(p[p > 0] * np.log(p[p > 0])))
        end = int(np.ceil(.5 * rank))
        ends.append(end)
        images.append(np.abs((matrix @ vectors).T[:end]).sum(axis=0).reshape(2, 2))
    assert ends[0] != ends[1]
    np.testing.assert_allclose(
        pca_packet_mean(np, frames, 4, [0, '0.5*"effective rank"']),
        np.mean(images, axis=0),
    )


@pytest.mark.parametrize('eigenvalues, bounds, expected', [
    ([0, 0, 0, 0], [0, '0.1*"effective rank"'], (0, 0)),
    ([-1e-10, 0, 0, 9], [0, '0.1*"effective rank"'], (0, 1)),
    ([1, 1, 1, 1], [0, '100*"effective rank"'], (0, 4)),
    ([1, 1, 1, 1], ['0.25*"effective rank"', 4], (1, 4)),
])
def test_rank_bounds(eigenvalues, bounds, expected):
    assert _resolve_pca_index_range(np, bounds, np.array(eigenvalues)) == expected


def test_zero_packet_returns_zero_image():
    np.testing.assert_array_equal(
        pca_packet_mean(np, np.zeros((4, 2, 3)), 4, [0, '0.1*"effective rank"']),
        np.zeros((2, 3)),
    )


@pytest.mark.parametrize('bound', [True, 1.5, '-0.1*"effective rank"',
                                  'nan*"effective rank"', '1e999*"effective rank"',
                                  '__import__("os")', '0.1*other'])
def test_invalid_bounds(bound):
    with pytest.raises((TypeError, ValueError)):
        validate_pca_index_range([0, bound], 4)


def test_reversed_resolved_bounds_are_rejected():
    with pytest.raises(ValueError, match='pca_index_range'):
        pca_packet_mean(np, np.ones((4, 2, 3)), 4, [2, '0*"effective rank"'])


def test_optional_eigenvalues_preserve_transform():
    frames = np.random.default_rng(1).normal(size=(4, 2, 3))
    projected, values = pca_time_transform(np, frames, return_eigenvalues=True)
    np.testing.assert_allclose(projected, pca_time_transform(np, frames))
    np.testing.assert_allclose(values, np.linalg.eigvalsh(frames.reshape(4, -1) @ frames.reshape(4, -1).T))
