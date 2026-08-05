"""Space, depth, aperture, frequency, and axial SVD routines."""

from __future__ import annotations

from typing import Any, Literal

from ._backend import array_namespace
from .types import AxialSVDResult, GouyCorrelationResult, SVDResult


SVDMethod = Literal["gram", "randomized"]


def _validate_rank(rank: int | None, maximum: int) -> int:
    if rank is None:
        return maximum
    rank = int(rank)
    if rank < 1 or rank > maximum:
        raise ValueError(f"rank must lie between 1 and {maximum}.")
    return rank


def _gram_svd(X: Any, rank: int) -> tuple[Any, Any, Any]:
    """Exact SVD through the smaller Hermitian Gram matrix."""

    xp = array_namespace(X)
    m, n = X.shape
    if m >= n:
        gram = X.conj().T @ X
        eigenvalues, right_modes = xp.linalg.eigh(gram)
        order = xp.argsort(eigenvalues)[::-1][:rank]
        eigenvalues = xp.maximum(xp.real(eigenvalues[order]), 0)
        right_modes = right_modes[:, order]
        singular_values = xp.sqrt(eigenvalues)
        tolerance = xp.finfo(singular_values.dtype).eps * max(m, n) * xp.maximum(
            singular_values[0], 1
        )
        safe = xp.where(singular_values > tolerance, singular_values, 1)
        left_modes = (X @ right_modes) / safe[None, :]
        left_modes = xp.where(
            (singular_values > tolerance)[None, :], left_modes, 0
        )
        right_modes_h = right_modes.conj().T
    else:
        gram = X @ X.conj().T
        eigenvalues, left_modes = xp.linalg.eigh(gram)
        order = xp.argsort(eigenvalues)[::-1][:rank]
        eigenvalues = xp.maximum(xp.real(eigenvalues[order]), 0)
        left_modes = left_modes[:, order]
        singular_values = xp.sqrt(eigenvalues)
        tolerance = xp.finfo(singular_values.dtype).eps * max(m, n) * xp.maximum(
            singular_values[0], 1
        )
        safe = xp.where(singular_values > tolerance, singular_values, 1)
        right_modes_h = (left_modes.conj().T @ X) / safe[:, None]
        right_modes_h = xp.where(
            (singular_values > tolerance)[:, None], right_modes_h, 0
        )
    return left_modes, singular_values, right_modes_h


def _randomized_svd(
    X: Any,
    rank: int,
    *,
    oversamples: int,
    power_iterations: int,
    seed: int | None,
) -> tuple[Any, Any, Any]:
    """Explicit opt-in randomized truncated SVD."""

    xp = array_namespace(X)
    m, n = X.shape
    sample_rank = min(rank + int(oversamples), min(m, n))
    if sample_rank < rank:
        raise ValueError("The randomized sample rank is smaller than rank.")
    if power_iterations < 0:
        raise ValueError("power_iterations must be nonnegative.")

    rng = xp.random.default_rng(seed)
    omega = rng.standard_normal((n, sample_rank))
    if X.dtype.kind == "c":
        omega = omega + 1j * rng.standard_normal((n, sample_rank))
    omega = omega.astype(X.dtype, copy=False)
    sample = X @ omega
    for _ in range(power_iterations):
        sample = X @ (X.conj().T @ sample)
    basis, _ = xp.linalg.qr(sample, mode="reduced")
    small = basis.conj().T @ X
    left_small, singular_values, right_modes_h = xp.linalg.svd(
        small, full_matrices=False
    )
    return (
        (basis @ left_small[:, :rank]),
        singular_values[:rank],
        right_modes_h[:rank],
    )


def matrix_svd(
    X: Any,
    *,
    rank: int | None = None,
    center_rows: bool = False,
    method: SVDMethod = "gram",
    oversamples: int = 8,
    power_iterations: int = 2,
    seed: int | None = 0,
) -> SVDResult:
    """Decompose a two-dimensional real or complex matrix.

    ``method='gram'`` is exact; ``rank`` only truncates the returned triplets.
    ``method='randomized'`` is an explicit approximate option and requires a
    finite rank.
    """

    if getattr(X, "ndim", 0) != 2:
        raise ValueError("X must be a two-dimensional matrix.")
    if X.shape[0] < 1 or X.shape[1] < 1:
        raise ValueError("X cannot contain an empty dimension.")
    xp = array_namespace(X)
    working = X - xp.mean(X, axis=1, keepdims=True) if center_rows else X
    maximum = min(working.shape)
    selected_rank = _validate_rank(rank, maximum)

    if method == "gram":
        left, singular_values, right_h = _gram_svd(working, selected_rank)
    elif method == "randomized":
        if rank is None:
            raise ValueError("Randomized SVD requires an explicit rank.")
        left, singular_values, right_h = _randomized_svd(
            working,
            selected_rank,
            oversamples=oversamples,
            power_iterations=power_iterations,
            seed=seed,
        )
    else:
        raise ValueError(f"Unsupported SVD method: {method!r}.")

    return SVDResult(
        left_modes=left,
        singular_values=singular_values,
        right_modes_h=right_h,
        matrix_shape=(int(X.shape[0]), int(X.shape[1])),
        centered_rows=bool(center_rows),
        method=str(method),
    )


def _unfold_time_first(
    array: Any,
    *,
    expected_ndim: int,
    sample_mask: Any | None,
    sample_weights: Any | None,
):
    """Put a time-first array's fixed sample coordinates along matrix rows."""

    if getattr(array, "ndim", 0) != expected_ndim:
        raise ValueError(f"Expected a {expected_ndim}-dimensional time-first array.")
    xp = array_namespace(array, sample_mask, sample_weights)
    sample_shape = array.shape[1:]
    matrix = array.reshape(array.shape[0], -1).T
    selected = None
    if sample_mask is not None:
        mask = xp.asarray(sample_mask, dtype=bool)
        if mask.shape != sample_shape:
            raise ValueError(
                f"sample_mask must have shape {sample_shape}, got {mask.shape}."
            )
        selected = mask.reshape(-1)
        matrix = matrix[selected]
        if matrix.shape[0] == 0:
            raise ValueError("sample_mask does not retain any samples.")
    if sample_weights is not None:
        weights = xp.asarray(sample_weights)
        if weights.shape != sample_shape:
            raise ValueError(
                f"sample_weights must have shape {sample_shape}, got {weights.shape}."
            )
        weights = weights.reshape(-1)
        if selected is not None:
            weights = weights[selected]
        matrix = matrix * weights[:, None]
    return matrix


def unfold_space_time(
    H: Any,
    *,
    sample_mask: Any | None = None,
    sample_weights: Any | None = None,
):
    """Convert ``H[t, y, x]`` to ``X[r, t]`` in C-order spatial indexing."""

    if getattr(H, "ndim", 0) != 3:
        raise ValueError("H must have shape (N_t, N_y, N_x).")
    return _unfold_time_first(
        H,
        expected_ndim=3,
        sample_mask=sample_mask,
        sample_weights=sample_weights,
    )


def unfold_depth_time(
    H_z: Any,
    *,
    sample_mask: Any | None = None,
    sample_weights: Any | None = None,
):
    """Convert ``H_z[t, z, y, x]`` to ``X[(z,r), t]``."""

    if getattr(H_z, "ndim", 0) != 4:
        raise ValueError("H_z must have shape (N_t, N_z, N_y, N_x).")
    return _unfold_time_first(
        H_z,
        expected_ndim=4,
        sample_mask=sample_mask,
        sample_weights=sample_weights,
    )


def unfold_depth_aperture_time(
    H_zp: Any,
    *,
    sample_mask: Any | None = None,
    sample_weights: Any | None = None,
):
    """Convert ``H_zp[t, z, p, y, x]`` to ``X[(z,p,r), t]``."""

    if getattr(H_zp, "ndim", 0) != 5:
        raise ValueError("H_zp must have shape (N_t, N_z, N_p, N_y, N_x).")
    return _unfold_time_first(
        H_zp,
        expected_ndim=5,
        sample_mask=sample_mask,
        sample_weights=sample_weights,
    )


def space_time_svd(
    H: Any,
    *,
    sample_mask: Any | None = None,
    sample_weights: Any | None = None,
    **kwargs: Any,
) -> SVDResult:
    """SVD of the established time-first field stack."""

    return matrix_svd(
        unfold_space_time(
            H, sample_mask=sample_mask, sample_weights=sample_weights
        ),
        **kwargs,
    )


def depth_time_svd(
    H_z: Any,
    *,
    sample_mask: Any | None = None,
    sample_weights: Any | None = None,
    **kwargs: Any,
) -> SVDResult:
    """Joint space-depth/time SVD."""

    return matrix_svd(
        unfold_depth_time(
            H_z, sample_mask=sample_mask, sample_weights=sample_weights
        ),
        **kwargs,
    )


def depth_aperture_time_svd(
    H_zp: Any,
    *,
    sample_mask: Any | None = None,
    sample_weights: Any | None = None,
    **kwargs: Any,
) -> SVDResult:
    """Joint space-depth-aperture/time SVD."""

    return matrix_svd(
        unfold_depth_aperture_time(
            H_zp, sample_mask=sample_mask, sample_weights=sample_weights
        ),
        **kwargs,
    )


def band_limited_svd(
    H: Any,
    frequency_mask: Any,
    *,
    nfft: int | None = None,
    **kwargs: Any,
) -> SVDResult:
    """SVD after a right-side temporal Fourier transform and band projection."""

    if getattr(H, "ndim", 0) < 3:
        raise ValueError("H must have shape (N_t, ..., N_y, N_x).")
    xp = array_namespace(H, frequency_mask)
    if nfft is None:
        nfft = H.shape[0]
    if nfft != H.shape[0]:
        raise ValueError("nfft must equal N_t for the manuscript's unitary transform.")
    SH = xp.fft.fft(H, n=nfft, axis=0, norm="ortho")
    mask = xp.asarray(frequency_mask, dtype=bool)
    if mask.shape != (nfft,):
        raise ValueError("frequency_mask must have shape (N_t,).")
    selected = SH[mask]
    matrix = selected.reshape(selected.shape[0], -1).T
    return matrix_svd(matrix, **kwargs)


def depth_spectral_power_svd(S_z: Any, **kwargs: Any) -> SVDResult:
    """SVD of ``S_z[f, z, y, x]`` into space-depth and spectral modes."""

    if getattr(S_z, "ndim", 0) != 4:
        raise ValueError("S_z must have shape (N_f, N_z, N_y, N_x).")
    matrix = S_z.reshape(S_z.shape[0], -1).T
    return matrix_svd(matrix, **kwargs)


def axial_mode_svd(H_z: Any, **kwargs: Any) -> AxialSVDResult:
    """Put depth along columns and return spatial-temporal and axial modes."""

    if getattr(H_z, "ndim", 0) != 4:
        raise ValueError("H_z must have shape (N_t, N_z, N_y, N_x).")
    nt, nz, ny, nx = map(int, H_z.shape)
    matrix = H_z.transpose(0, 2, 3, 1).reshape(nt * ny * nx, nz)
    decomposition = matrix_svd(matrix, **kwargs)
    rank = decomposition.rank
    spatiotemporal = decomposition.left_modes.reshape(nt, ny, nx, rank).transpose(
        3, 0, 1, 2
    )
    axial_modes = decomposition.right_modes_h.conj().T
    return AxialSVDResult(
        decomposition=decomposition,
        spatiotemporal_modes=spatiotemporal,
        axial_modes=axial_modes,
        input_shape=(nt, nz, ny, nx),
    )


def gouy_symmetric_depth_correlation(axial_modes: Any, half_width: int):
    """Return manuscript correlation ``rho[k,m]`` for axial modes ``Z[z,m]``."""

    if getattr(axial_modes, "ndim", 0) != 2:
        raise ValueError("axial_modes must have shape (N_z, N_mode).")
    nz, number_of_modes = axial_modes.shape
    if half_width < 1 or 2 * half_width >= nz:
        raise ValueError("half_width must satisfy 1 <= 2*half_width < N_z.")
    xp = array_namespace(axial_modes)
    nan_value = complex(float("nan"), float("nan"))
    correlation = xp.full(
        (nz, number_of_modes), nan_value, dtype=axial_modes.dtype
    )
    for center in range(half_width, nz - half_width):
        positive = axial_modes[center + 1 : center + half_width + 1]
        negative = axial_modes[center - half_width : center][::-1]
        numerator = xp.sum(positive * xp.conj(negative), axis=0)
        positive_energy = xp.sum(xp.abs(positive) ** 2, axis=0)
        negative_energy = xp.sum(xp.abs(negative) ** 2, axis=0)
        denominator = xp.sqrt(positive_energy * negative_energy)
        correlation[center] = xp.where(denominator > 0, numerator / denominator, nan_value)
    return correlation


def rank_gouy_candidates(
    correlation: Any,
    *,
    half_width: int,
    depths: Any | None = None,
    top_k: int = 3,
) -> GouyCorrelationResult:
    """Rank negative-real symmetric correlations as candidate phase reversals."""

    if getattr(correlation, "ndim", 0) != 2:
        raise ValueError("correlation must have shape (N_z, N_mode).")
    if top_k < 1:
        raise ValueError("top_k must be positive.")
    xp = array_namespace(correlation, depths)
    finite = xp.isfinite(xp.real(correlation)) & xp.isfinite(xp.imag(correlation))
    score = xp.where(finite, xp.maximum(-xp.real(correlation), 0), 0)
    valid_indices = xp.arange(half_width, correlation.shape[0] - half_width)
    count = min(top_k, int(valid_indices.shape[0]))
    per_mode_scores = score[valid_indices].T
    local_order = xp.argsort(per_mode_scores, axis=1)[:, ::-1][:, :count]
    candidate_indices = valid_indices[local_order]
    candidate_scores = xp.take_along_axis(per_mode_scores, local_order, axis=1)
    candidate_depths = None
    if depths is not None:
        depths = xp.asarray(depths)
        if depths.shape != (correlation.shape[0],):
            raise ValueError("depths must have shape (N_z,).")
        candidate_depths = depths[candidate_indices]
    return GouyCorrelationResult(
        correlation=correlation,
        score=score,
        candidate_indices=candidate_indices,
        candidate_scores=candidate_scores,
        candidate_depths=candidate_depths,
        half_width=int(half_width),
    )


def analyze_axial_gouy(
    axial_modes: Any,
    *,
    half_width: int,
    depths: Any | None = None,
    top_k: int = 3,
) -> GouyCorrelationResult:
    """Return both raw Gouy correlations and ranked candidate planes."""

    correlation = gouy_symmetric_depth_correlation(axial_modes, half_width)
    return rank_gouy_candidates(
        correlation,
        half_width=half_width,
        depths=depths,
        top_k=top_k,
    )
