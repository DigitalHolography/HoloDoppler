# Multidimensional processing

This package implements the analysis definitions in
`MultidimensionalProcessing.tex` while preserving HoloDoppler's existing
time-first and unshifted-frequency conventions. CuPy/CUDA 13 is the production
target. NumPy follows the same API for small deterministic reference tests.

## Axis and dtype contract

| Quantity | Shape | Meaning |
|---|---:|---|
| Full-aperture field | `H[t, y, x]` | Existing reconstructed complex field |
| Aperture field | `H_p[t, p, y, x]` | `p = [NW, NE, SW, SE]` |
| Depth field | `H_z[t, z, y, x]` | Repeated reconstruction distances |
| Depth/aperture field | `H_zp[t, z, p, y, x]` | Joint coordinate stack |
| Existing single estimate | `SH[f, y, x]` | Unshifted temporal FFT order |
| New spectral estimates | `SH[e, f, ..., y, x]` | Window/taper estimate first |
| Quadrant cross spectrum | `C[f, y, x, p, q]` | Matrix axes are last |

The spatial flattening used by SVD is C order, `n = y * N_x + x`. New code
defaults to `complex64` and `float32` when its input has those dtypes. Frequency
coordinates may remain `float64`; they are small coordinate arrays and do not
promote field or spectral arrays.

Temporal frequencies follow `fftfreq` order:
`[0, positive frequencies, negative frequencies]`. The routines do not call
`fftshift` on the temporal axis. Symmetric bands select on `abs(f)` without
changing bin order, matching previous HoloDoppler processing.

`Holodoppler.render_holograms(parameters)` exposes the complex reconstruction
before the legacy SVD filter, temporal FFT, and moment calculation.
`Holodoppler.render_holograms_at_depths(parameters, depths)` produces
`H_z[t, z, y, x]`. The latter stacks every requested depth in memory; for a
large depth scan, call `render_holograms` one depth at a time and keep only the
needed crop or derived quantity.

## Manuscript-to-API mapping

| Analysis | Public routine |
|---|---|
| Complex, centered log-amplitude, phase phasor | `build_field_representations` |
| Fixed phase-validity mask | `phase_validity_mask` |
| Energy-normalized DPSS/Hann/boxcar estimates | `temporal_spectral_estimates` |
| Amplitude–phase cross-spectrum and coherence | `representation_coupling` |
| Balanced fixed quadrant masks | `quadrant_masks` |
| Reciprocal-plane aperture selection | `apply_aperture_masks` |
| Power asymmetries | `power_asymmetries` |
| Quadrant cross-spectral matrix | `quadrant_cross_spectral_matrix` |
| Hadamard modal matrix and contrasts | `analyze_quadrant_spectra` |
| Band-first angular normalization | `band_angular_analysis` |
| Arbitrary fractional aperture delays | `delayed_recombination_spectra` |
| Reciprocal one-frame delay contrast | `one_frame_reciprocal_analysis` |
| Space/time and joint unfoldings | `unfold_space_time`, `unfold_depth_time`, `unfold_depth_aperture_time` |
| Exact or truncated SVD | `matrix_svd` and the `*_svd` wrappers |
| Band-limited SVD | `band_limited_svd` |
| Axial modes and Gouy candidates | `axial_mode_svd`, `analyze_axial_gouy` |
| Selected HDF5 results | `save_analysis_h5` |
| Selected 2-D diagnostic PNGs | `export_diagnostic_images` |

## Defaults and validity rules

- The default and minimum temporal block length is 32 samples.
- The default estimator uses four unit-energy DPSS tapers with
  time-bandwidth product 2.5.
- Coherence requires at least two spectral estimates. A single Hann or boxcar
  window can estimate power but cannot provide informative coherence.
- The phase-validity threshold is one percent of the spatial median of the
  time-averaged nonzero power. A fixed caller-provided mask can further limit
  it.
- `analyze_field_block` excludes DC from amplitude–phase coherence by default.
  Set `coupling_low_frequency_guard` to exclude a larger symmetric guard band.
- Normalized quantities are `NaN` outside their validity support; invalid
  values are never silently replaced with zero.
- Aperture masks are fixed in the centered reciprocal plane. Default masks
  require equal usable support. Supply an explicit center, radius, or fixed
  support mask when the optical pupil does not fill a balanced rectangle.

## SVD preprocessing

`matrix_svd` performs no implicit centering. Use `center_rows=True` when
fluctuation modes are intended, especially for the uncentered phase phasor.
The default `method="gram"` is deterministic and returns the exact Gram-matrix
decomposition. `rank=N` truncates the returned singular triplets. For a large
explicitly truncated problem, `method="randomized"` is an opt-in approximate
alternative and requires a rank.

The unfolding and SVD wrappers accept fixed `sample_mask` and
`sample_weights` arrays matching all non-time axes. This implements the
manuscript's time-invariant region selection and block weighting before the
decomposition. The caller must report those choices with the result.

## Large-data workflow

`temporal_spectral_estimates` intentionally returns the individual estimates
needed for reproducible cross-spectra and coherence. Check the allocation
before computing it:

```python
from holodoppler.multidimensional import (
    spectral_estimate_nbytes,
    spectral_estimate_shape,
)

shape = spectral_estimate_shape(H.shape, block_length=32, number_of_tapers=4)
nbytes = spectral_estimate_nbytes(H.shape, block_length=32, number_of_tapers=4)
print(shape, nbytes / 2**30, "GiB")
```

Begin with exactly one 32-frame block. Aperture-resolved spectra contain an
additional axis of length four, and the three representations each retain a
separate spectral array. Increase the block count, crop, or selected channels
only after checking available VRAM. Do not transfer complete intermediate
arrays to the host merely for plotting.

## Selective export

Computation, persistent export, and visualization are separate. Export only
chosen quantities, preferably band-summed or cropped results:

```python
from holodoppler.multidimensional import save_analysis_h5

save_analysis_h5(
    "outside-the-repository/selected_results.h5",
    {
        "full_field": {
            "amplitude_phase_coherence": result.amplitude_phase_coupling.coherence,
        },
        "angular": {
            "complex_field_asymmetries": result.angular["H"].normalized_power_asymmetries,
            "complex_field_interference": result.angular["H"].interference_contrasts,
        },
    },
    metadata={
        "sampling_frequency_hz": parameters["sampling_freq"],
        "block_length": 32,
        "frequency_order": "unshifted",
    },
)
```

`export_diagnostic_images` accepts only caller-selected 2-D arrays. Slice or
band-reduce multidimensional results before calling it.

## Real-recording validation

Recordings may vary in frame dimensions and sampling rate. `load_file` clears
propagation kernels, and `render_holograms` validates the kernel signature so
changing reconstruction distance or dimensions cannot silently reuse an
incompatible kernel. Always take `sampling_freq`, propagation parameters,
frame dimensions, and frame range from the recording-specific configuration.

Before accepting a real-data result, record the input and output shapes,
dtypes, selected mask/support, number of estimates, frequency bins, estimated
RAM/VRAM, temporary disk use, and exported size. Validate in this order:

1. one 32-frame synthetic block on NumPy;
2. the same synthetic block on CuPy and compare tolerances;
3. one short local `.holo` block without optional export;
4. selected reduced diagnostics and HDF5 export;
5. only then increase the dataset size.
