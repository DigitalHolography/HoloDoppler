#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
service=cpu
build=false
mode=process
recursive=false
for argument in "$@"; do
    case "$argument" in
        --gpu) service=gpu ;;
        --build) build=true ;;
        --preview) mode=preview ;;
        --recursive) recursive=true ;;
        --help|-h)
            echo 'Usage: sh run.sh [--gpu] [--build] [--preview] [--recursive]'
            exit 0 ;;
        *) echo "Unknown option: $argument" >&2; exit 2 ;;
    esac
done
command -v docker >/dev/null 2>&1 || {
    echo 'Install and start Docker with the Compose plugin first.' >&2
    exit 1
}
mkdir -p "$script_dir/input" "$script_dir/config" "$script_dir/output"
test -f "$script_dir/config/parameters.yaml" || {
    echo 'Missing config/parameters.yaml. Restore the default settings from the starter download.' >&2
    exit 1
}
docker_os=$(docker info --format '{{.OSType}}') || {
    echo 'Docker is unavailable. Start its Linux engine and try again.' >&2
    exit 1
}
if [ "$docker_os" != linux ]; then
    echo 'Switch Docker to Linux containers and try again.' >&2
    exit 1
fi

# Host-created directories and the host UID/GID keep results owned by the user.
export HOLODOPPLER_UID="$(id -u)"
export HOLODOPPLER_GID="$(id -g)"
set -- -f "$script_dir/compose.yaml"
if "$build"; then
    test -f "$script_dir/compose.build.yaml" || {
        echo '--build needs the source repository. Starter users can run without --build.' >&2
        exit 1
    }
    set -- "$@" -f "$script_dir/compose.build.yaml"
    docker compose "$@" build "$service"
fi
set -- "$@" run --rm --no-deps "$service" "$mode" --folder /data /config/parameters.yaml --output-dir /output
if [ "$service" = gpu ]; then set -- "$@" --require-gpu; fi
if "$recursive"; then set -- "$@" --recursive; fi
exec docker compose "$@"
