# LSCI

LSCI emits full-resolution STD, MEAN and RATIO maps. Each output uses a complete
window of lsci_time_window_size consecutive frames, moving its start by
lsci_time_window_stride source frames. Incomplete final windows are omitted.
A temporal size of 1 computes spatial contrast only.

Statistics use the joint temporal and square spatial neighborhood configured by
lsci_pixel_window_size and its boundary mode/cval. STD is population standard
deviation; RATIO is STD / max(MEAN, 1e-6), with a fixed epsilon. Each RATIO map is clipped
to its own 1st and 99th percentiles without rescaling. Preview displays RATIO.
Legacy flow-index, history, resize and batch settings no longer control LSCI.
