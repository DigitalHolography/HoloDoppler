# syntax=docker/dockerfile:1

# Build with --target cpu (default), gpu, gui-cpu, or gui-gpu.
ARG PYTHON_IMAGE=python:3.13-slim-bookworm

FROM ${PYTHON_IMAGE} AS build
WORKDIR /build
RUN python -m venv /opt/venv
COPY pyproject.toml README.md ./
COPY requirements/ ./requirements/
COPY holodoppler/ ./holodoppler/
RUN /opt/venv/bin/python -m pip install --no-cache-dir --only-binary=:all: \
        -r requirements/cli-cpu-linux-py313.txt \
    && /opt/venv/bin/python -m pip install --no-cache-dir --no-deps . \
    && /opt/venv/bin/python -m pip check

FROM build AS build-gpu
RUN /opt/venv/bin/python -m pip install --no-cache-dir --only-binary=:all: \
        -r requirements/cli-gpu-linux-py313.txt \
    && /opt/venv/bin/python -m pip check

FROM build AS build-gui
RUN /opt/venv/bin/python -m pip install --no-cache-dir --only-binary=:all: \
        -r requirements/gui-linux-py313.txt \
    && /opt/venv/bin/python -m pip check

FROM build-gpu AS build-gpu-gui
RUN /opt/venv/bin/python -m pip install --no-cache-dir --only-binary=:all: \
        -r requirements/gui-linux-py313.txt \
    && /opt/venv/bin/python -m pip check

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

# The regular OpenCV wheel requires these shared libraries on Debian slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 holodoppler \
    && useradd --uid 10001 --gid 10001 --create-home holodoppler \
    && mkdir -p /data /config /output \
    && chown holodoppler:holodoppler /output

WORKDIR /app
COPY parameters/ ./parameters/
COPY docker/config/parameters.yaml /config/parameters.yaml
USER 10001:10001
ENTRYPOINT ["holodoppler"]
CMD ["--help"]

FROM runtime AS gpu
COPY --from=build-gpu /opt/venv /opt/venv
CMD ["process", "--folder", "/data", "/config/parameters.yaml", "--output-dir", "/output", "--require-gpu"]

FROM runtime AS gui-runtime
# The slim Python image includes _tkinter but removes its Tcl/Tk shared
# libraries. Install them and a fallback font only in the GUI variants.
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tk8.6 tcl8.6 libxcursor1 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
USER 10001:10001
CMD ["gui"]

FROM gui-runtime AS gui-cpu
COPY --from=build-gui /opt/venv /opt/venv

FROM gui-runtime AS gui-gpu
COPY --from=build-gpu-gui /opt/venv /opt/venv

FROM runtime AS cpu
COPY --from=build /opt/venv /opt/venv
CMD ["process", "--folder", "/data", "/config/parameters.yaml", "--output-dir", "/output"]
