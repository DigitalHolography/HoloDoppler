# Linux Docker images

The Dockerfile has four targets. `cpu` is the default and contains the NumPy
backend. `gpu` adds CuPy and the CUDA 13 component wheels. `gui-cpu` and
`gui-gpu` add Tkinter, the GUI dependencies, and the Tcl/Tk runtime. The GUI
targets launch `holodoppler gui` by default; the CLI targets print `--help` by
default. None exposes a port or runs a daemon. The images currently target
Linux `amd64` and Python 3.13.

| Image | Use for |
| --- | --- |
| `cpu` | The `simple`, `sh_avg`, and `sliding_shack_hartmann` pipelines with NumPy. |
| `gpu` | The same pipelines with CuPy available for CUDA processing. |
| `gui-cpu` | The desktop GUI with the NumPy backend. |
| `gui-gpu` | The desktop GUI with CuPy available for CUDA processing. |

The `spectral_cube`, `pca_accumulation`, and `split_apertures` pipeline modules
currently import legacy names that are absent from `holodoppler.saving`. They
need application fixes and processing tests before a GPU image can be released
for those pipelines. Containerizing them does not resolve those import errors.

## Build

Install Docker Engine on the Linux machine, then run these commands from the
repository root:

```sh
docker build --pull --target cpu -t holodoppler:1.0-cpu .
docker build --pull --target gpu -t holodoppler:1.0-gpu .
docker build --pull --target gui-cpu -t holodoppler:1.0-gui-cpu .
docker build --pull --target gui-gpu -t holodoppler:1.0-gui-gpu .
docker run --rm holodoppler:1.0-cpu --help
```

The GPU build does not need a GPU. Running it on a GPU requires a compatible
NVIDIA driver and NVIDIA Container Toolkit on the **host**. The current CUDA
13 dependency needs an NVIDIA driver in the 580 series or newer. Check the
driver compatibility table when updating the CUDA lock file. The CUDA toolkit
libraries are already included in the GPU image through CuPy's `ctk` extra.

Check GPU access on the target machine before processing data:

```sh
docker run --rm --gpus all --entrypoint python holodoppler:1.0-gpu \
  -c 'import cupy as cp; print(cp.arange(3).get())'
```

## Process a file

Put input files and any custom YAML configuration under `data/`. Create a
separate host directory for results:

```sh
mkdir -p data results
docker run --rm --init \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
  --mount type=bind,src="$(pwd)/results",dst=/output \
  holodoppler:1.0-cpu \
  process /data/recording.holo /app/parameters/default_parameters_simple.yaml \
  --output-dir /output/recording
```

The paths passed to `holodoppler` must be **container paths** such as `/data`
and `/output`. `--output-dir` directs generated files into the writable
mount, leaving input data read-only. The same option works with `preview`.
Running with the host UID/GID lets the process write to `results/` without
creating root-owned files. The container has no special privileges by default.

For the GPU image, add `--gpus all` before the image name. Use a YAML file with
`use_parallel: false` and `force_numpy: false` when processing the `simple`,
`sh_avg`, or `sliding_shack_hartmann` pipeline on the GPU. The bundled
`default_parameters_simple.yaml` sets `use_parallel: true`, which selects the
NumPy processing path even if a GPU is available. Edit a copy under `data/`
and pass its container path, for example `/data/gpu.yaml`.

For batch mode, create a UTF-8 text file with one **container path** per line,
such as `/data/recording.holo`, then run:

```sh
docker run --rm --init \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
  --mount type=bind,src="$(pwd)/results",dst=/output \
  holodoppler:1.0-cpu \
  process --batch /data/files.txt /app/parameters/default_parameters_simple.yaml \
  --output-dir /output
```

Batch results go under `/output/<file-stem>_<path-hash>/` to prevent files
with the same name in different input directories from overwriting each other.
The job exits nonzero if any file fails.

## Run the GUI

The GUI needs an X11 display server on the host. The image contains the GUI
software, but a display connection must be passed to the container at run
time. On a Linux desktop with an X11 or XWayland display, run:

```sh
mkdir -p data results gui-config
xauth_file="${XAUTHORITY:-$HOME/.Xauthority}"
test -f "$xauth_file"  # use the active Xauthority file for your desktop session
docker run --rm --init \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e XDG_CONFIG_HOME=/config \
  -e DISPLAY -e XAUTHORITY=/tmp/.Xauthority \
  --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix \
  --mount type=bind,src="$xauth_file",dst=/tmp/.Xauthority,readonly \
  --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
  --mount type=bind,src="$(pwd)/results",dst=/output \
  --mount type=bind,src="$(pwd)/gui-config",dst=/config \
  holodoppler:1.0-gui-cpu
```

Open files from `/data` in the file picker. Before processing, set the GUI's
**Advanced → Output → `saving_to_folder`** parameter to `/output` and save the
settings; the default output location is beside the input file, which is
read-only in this example. GUI settings persist in `gui-config/` and results
appear in `results/`. Use `holodoppler:1.0-gui-gpu` and add `--gpus all` before
the image name for GPU processing. For GPU pipelines, set `use_parallel: false`
and `force_numpy: false` in the selected parameters.

On Windows, run the GUI image from a WSL distribution with WSLg and Docker
Desktop's WSL integration. From the repository root in the WSL shell, run:

```sh
mkdir -p data results gui-config
docker run --rm --init \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e XDG_CONFIG_HOME=/config -e DISPLAY \
  --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix \
  --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
  --mount type=bind,src="$(pwd)/results",dst=/output \
  --mount type=bind,src="$(pwd)/gui-config",dst=/config \
  holodoppler:1.0-gui-cpu
```

WSLg provides the X11 socket and `DISPLAY`. Building the image in PowerShell
is also possible; the run command above belongs in the WSL shell. Add
`--gpus all` and use `holodoppler:1.0-gui-gpu` for GPU processing.

## Maintain and release

1. Update `pyproject.toml` when direct dependencies change. Regenerate the
   pinned Linux dependency lists using `uv`, and review the diffs:

   ```sh
   uv pip compile pyproject.toml --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --only-binary :all: --output-file requirements/cli-cpu-linux-py313.txt
   uv pip compile pyproject.toml --extra gpu --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --only-binary :all: --output-file requirements/cli-gpu-linux-py313.txt
   uv pip compile pyproject.toml --extra gui --constraints requirements/cli-cpu-linux-py313.txt --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --only-binary :all: --output-file requirements/gui-linux-py313.txt
   ```

2. Build all four targets in CI. Run `--help`, import checks, and a GUI startup
   check on a virtual display in ordinary CI. Run at least one real processing
   job for each backend before publishing a release. GPU execution must be
   checked on a GPU-equipped Linux host.
3. Update the Python base image regularly. For strict rebuild
   reproducibility, replace its version tag with a reviewed image digest and
   update that digest in a pull request. Rebuild on security updates, even if
   HoloDoppler code has not changed.
4. Publish separate immutable versioned tags such as `1.0-cpu`, `1.0-gpu`,
   `1.0-gui-cpu`, and `1.0-gui-gpu`, plus a commit identifier. Deploy a tested
   registry digest to production;
   avoid `latest` as a deployment reference. Keep data, configuration, and
   results in bind mounts, never in the image.

For example, after authenticating to your registry and validating the image,
publish the CPU variant to GitHub Container Registry with:

```sh
docker tag holodoppler:1.0-cpu ghcr.io/your-org/holodoppler:1.0-cpu
docker push ghcr.io/your-org/holodoppler:1.0-cpu
```

Use the same pattern for the GPU variant after its GPU-host processing check.
Inspect the pushed image's digest in the registry and use that digest in
production run commands.

These containers are batch jobs, so a service health check or Compose file is
not needed. The CLI exit code is the job result.
