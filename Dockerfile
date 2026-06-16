# ── Base Image ────────────────────────────────────────────────────────────────
# Use the official slim Python image to keep the container lightweight.
# 'slim' strips out unnecessary system packages while retaining pip and stdlib.
FROM python:3.11-slim

# ── Metadata ──────────────────────────────────────────────────────────────────
LABEL maintainer="AeroGrid Data Engineering"
LABEL description="Turbine telemetry anomaly detection script"

# ── Working Directory ─────────────────────────────────────────────────────────
# All subsequent commands and the running container operate from /app.
WORKDIR /app

# ── Dependencies ──────────────────────────────────────────────────────────────
# Copy the requirements file first so Docker can cache this layer.
# Re-installing packages is only triggered if requirements.txt changes,
# not every time the source code changes — this speeds up rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application Code ──────────────────────────────────────────────────────────
# Copy the analysis script into the container image.
COPY analyse_turbines.py .

# ── Data Volume ───────────────────────────────────────────────────────────────
# The telemetry XLSX is NOT baked into the image (it changes every 24 hrs).
# VOLUME declares /app as a mount point so the Docker daemon and orchestration
# tools (e.g. Kubernetes) know this directory is meant for external data.
# At runtime, bind-mount the directory containing telemetry_data.xlsx here:
#   docker run --rm -v /path/to/data:/app aerogrid-anomaly
VOLUME ["/app"]

# ── Entry Point ───────────────────────────────────────────────────────────────
# Run the anomaly detection script when the container starts.
CMD ["python", "analyse_turbines.py"]
