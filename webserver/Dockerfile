# ARGs for architecture and platform
ARG TARGETARCH=arm64
ARG TARGETPLATFORM=linux/arm64
ARG CHIPSET_ARCH=aarch64-linux-gnu

# ARGs for Python builder and Distroless base images
ARG PYTHON_BUILDER_IMAGE=python:3.11-slim
ARG GOOGLE_DISTROLESS_BASE_IMAGE=gcr.io/distroless/base-debian12
ARG CHIPSET_ARCH=aarch64-linux-gnu

# First stage: Build the Python app in a slim Python image
FROM ${PYTHON_BUILDER_IMAGE} AS python-base

# Install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install gcc g++ -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/tmp/huggingface_cache \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Create a non-root user and set up necessary directories
RUN groupadd -r clio && useradd -r -g clio clio && \
    mkdir -p /home/clio ${TRANSFORMERS_CACHE} && \
    chown -R clio:clio /home/clio ${TRANSFORMERS_CACHE}

# Install required packages
COPY requirements.txt /app/webserver/
RUN pip install --no-cache-dir -r /app/webserver/requirements.txt

# Copy the rest of the application code
COPY . /app/webserver

# Final stage: Use distroless base image
FROM ${GOOGLE_DISTROLESS_BASE_IMAGE}

# ARG for architecture
ARG CHIPSET_ARCH=aarch64-linux-gnu

# Copy Python and installed packages from the python-base image
COPY --from=python-base /usr/local/lib/ /usr/local/lib/
COPY --from=python-base /usr/local/bin/ /usr/local/bin/

# Copy necessary runtime libraries and binaries
COPY --from=python-base \
    /usr/lib/${CHIPSET_ARCH}/libz.so.1 \
    /usr/lib/${CHIPSET_ARCH}/libexpat* \
    /usr/lib/${CHIPSET_ARCH}/

COPY --from=python-base \
    /usr/lib/${CHIPSET_ARCH}/libffi* \
    /usr/lib/${CHIPSET_ARCH}/libgcc_s.so.1 \
    /usr/lib/${CHIPSET_ARCH}/libstdc++.so.6 \
    /usr/lib/${CHIPSET_ARCH}/
COPY --from=python-base /bin/echo /bin/ln /bin/rm /bin/sh /bin/

# Copy application and cache
COPY --from=python-base /app /app
COPY --from=python-base --chown=1000:1001 /tmp/huggingface_cache /tmp/huggingface_cache

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/tmp/huggingface_cache \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONFAULTHANDLER=1

# Use the non-root user
USER 1000:1001

WORKDIR /app

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "webserver.main:app"]