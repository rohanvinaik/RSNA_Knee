# Require a digest-pinned CPython image at build time. The final base image is an explicit input.
ARG PYTHON_BASE_IMAGE
FROM --platform=linux/amd64 ${PYTHON_BASE_IMAGE}

ARG SOURCE_REVISION
ARG SOURCE_TREE_SHA256
LABEL org.opencontainers.image.revision=${SOURCE_REVISION} \
      org.rsna-knee.source-tree-sha256=${SOURCE_TREE_SHA256} \
      org.rsna-knee.runtime-platform=linux/amd64

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TMPDIR=/tmp \
    XDG_CACHE_HOME=/scratch/cache \
    NUMBA_CACHE_DIR=/scratch/numba-cache \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMBA_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    BLIS_NUM_THREADS=1

WORKDIR /app
COPY requirements-runtime.txt /opt/requirements-runtime.txt
RUN python -m pip install --no-cache-dir --require-hashes --only-binary=:all: \
      --disable-pip-version-check -r /opt/requirements-runtime.txt
COPY source-manifest.json /app/source-manifest.json
COPY src/knee /app/src/knee
COPY scripts/run_interiors.py /app/scripts/run_interiors.py
RUN python -c "import gdcm, h5py, numba, numpy, pydicom, scipy, skimage; import knee.array_archive, knee.encoding.h5_store; from knee.objects.local_lightness import jit_local_lightness_kernel; assert callable(jit_local_lightness_kernel())"

ENTRYPOINT ["python", "/app/scripts/run_interiors.py"]
