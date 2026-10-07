# HoloDoppler CLI starter

Put your `.holo` recordings in `input/`. Edit `config/parameters.yaml` if needed,
then run a launcher. Results appear in `output/`, separately for each recording.
`.cine` recordings are also accepted.

```text
holodoppler-cli/
  input/                   put recordings here
  config/parameters.yaml   settings shared by all recordings
  output/                  results appear here
  run-cpu.cmd              Windows CPU launcher
  run-gpu.cmd              Windows NVIDIA GPU launcher
  run.ps1                  PowerShell launcher with extra options
  run.sh                   Linux / WSL launcher
  compose.yaml
```

## Windows

Install Docker Desktop, select its WSL 2 engine, and keep it running. GPU mode
also needs a compatible NVIDIA GPU and Windows driver. From PowerShell in
this folder, run:

```powershell
.\run-cpu.cmd
# Or:
.\run-gpu.cmd
```

The `.cmd` launchers run the included PowerShell script without requiring a
change to your machine's execution policy. Add `-Preview` for a quick preview,
or `-Recursive` to include recordings in subfolders.

## Linux / WSL

Install Docker with its Compose plugin. Linux GPU hosts also need NVIDIA
Container Toolkit configured for Docker. From this folder, run:

```sh
sh run.sh
# Or:
sh run.sh --gpu
```

Add `--preview` for previews, or `--recursive` to include subfolders. Run the
launcher as your normal user: it uses your UID/GID so results belong to you.
Use a local folder you can write to. On SELinux hosts, an administrator may
need to allow container access to the chosen bind mounts.

## Settings and results

The supplied `simple` pipeline settings work with either image. GPU mode needs
`use_parallel: false` and `force_numpy: false`; these are already set. CPU mode
uses NumPy automatically. GPU mode checks CUDA access before processing.

GPU runs retain compiled CuPy kernels in `output/.cupy-cache/`, so later
launches can reuse them. The first run with new operations, data types, or
dimensions can still be slower. This cache uses the writable output mount
and the same user as your results; no additional folder permissions are needed.

The `z`, `pixel_pitch`, and `sampling_freq` defaults read acquisition metadata
from each `.holo` footer (`use_holovibes`). If that metadata is missing, set
these values for your acquisition. Adjust frequency bands, propagation, batch
size, and SVD filtering for your data. A recording needs at least `batch_size`
frames to produce a full processing batch.

Autofocus (`shack_hartmann_autofocus: true`) runs once per recording, and ECC
registration (`image_registration_with_ecc: true`) runs after batch processing.
These can be substantial costs. Turn either off only if you do not need its
correction, and compare results first. Smaller `batch_size` values also change
frequency resolution and SVD filtering; choose them for the acquisition rather
than speed alone. See the source repository's `docs/docker.md` for performance
measurement and CPU tuning.

Input recordings and settings are mounted read-only. Only `output/` is writable.
The launchers create missing folders without overwriting settings. Recordings
run in filename order; individual failures are reported and the rest continue.
The job exits nonzero if any recording failed. Reruns reuse output names, so
move previous results aside if you want to keep them.

## Images and building from source

The starter uses these release images:

```text
ghcr.io/digitalholography/holodoppler:1.0-cpu
ghcr.io/digitalholography/holodoppler:1.0-gpu
```

The maintainer must publish these images before distributing the starter.
Docker pulls a missing image automatically; public images need no login.

In the source repository, build locally with:

```powershell
.\run-cpu.cmd -Build
.\run-gpu.cmd -Build
```

On Linux, use `sh run.sh --build` or `sh run.sh --build --gpu`. Building does
not need a GPU; running GPU jobs does. The build option needs the source repo.

To select another tag or a registry digest, set `HOLODOPPLER_CPU_IMAGE` and/or
`HOLODOPPLER_GPU_IMAGE` before launching. For example:

```powershell
$env:HOLODOPPLER_GPU_IMAGE = 'ghcr.io/digitalholography/holodoppler:1.1-gpu'
.\run-gpu.cmd
```

The `spectral_cube`, `pca_accumulation`, and `split_apertures` pipelines currently
have legacy import errors. Use `simple`, `sh_avg`, or `sliding_shack_hartmann`
with appropriately tested settings for this release.
