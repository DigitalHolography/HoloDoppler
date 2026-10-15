"""Validated scheduling of complete frame batches."""

from numbers import Integral


def calculate_batch_indices(first_frame, end_frame, batch_size, batch_stride, total_frames):
    """Return complete batch starts within an exclusive frame interval.

    An end of zero or less selects the end of the file.
    """
    for name, value in (
        ("first_frame", first_frame), ("end_frame", end_frame),
        ("batch_size", batch_size), ("batch_stride", batch_stride),
        ("total_frames", total_frames),
    ):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(f"{name} must be an integer; got {value!r}")
    if batch_size <= 0 or batch_stride <= 0:
        raise ValueError("batch_size and batch_stride must be positive")
    if total_frames < 0:
        raise ValueError("total_frames must be nonnegative")
    if not 0 <= first_frame <= total_frames:
        raise ValueError("first_frame must be between zero and total_frames")
    if end_frame <= 0:
        end_frame = total_frames
    if not first_frame <= end_frame <= total_frames:
        raise ValueError("end_frame must be between first_frame and total_frames")
    return range(first_frame, end_frame - batch_size + 1, batch_stride)
