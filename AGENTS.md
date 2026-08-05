# HoloDoppler development instructions

- Use Python 3.13 and the repository `.venv` for production work.
- Preserve NumPy compatibility for reference tests and CuPy/CUDA 13 compatibility for production.
- Keep the established array conventions: `H[t, y, x]` and unshifted `SH[f, y, x]`.
- Keep spatial axes as the final two axes in `(y, x)` order when adding depth, aperture, or estimate axes.
- Never modify or delete `.holo` or `.cine` recordings.
- Never commit recordings, local dataset paths, generated HDF5 files, videos, or diagnostic images.
- Run synthetic CPU tests before GPU or real-data tests.
- Begin real-data validation with one short temporal block.
- Before a large computation, report array shapes, dtypes, estimated RAM, VRAM, temporary disk, and output size.
- Keep numerical computation, persistent export, and diagnostic plotting in separate modules.
- Ask before adding a new required production dependency.
