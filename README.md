# AeroGrid Turbine Monitor

Anomaly detection service for offshore wind turbine telemetry data, built as part of the IEUK 2026 Bright Network Engineering Sector Skills Project (AeroGrid track).

## What it does

Parses 24-hour IoT sensor readings across a fleet of turbines and flags any unit exceeding safe operating thresholds:

- Average temperature > 85.0°C
- Any vibration spike > 15.0 mm/s

Results are printed as a formatted summary table with per-turbine status and maintenance reasons.

## Project structure

```
aerogrid-turbine-monitor/
├── analyse_turbines.py   # Anomaly detection script
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
├── engineering_report.docx  # Technical report addressed to AeroGrid CTO
└── README.md
```

> **Note:** `telemetry_data.xlsx` is not included in this repo. The script expects a file with columns `turbine_id`, `temperature_c`, and `vibration_mm_s` in the same directory.

## Running locally

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Place your telemetry file in the project directory**
```
telemetry_data.xlsx
```

**3. Run the script**
```bash
python analyse_turbines.py
```

**Example output:**
```
Loading data from 'telemetry_data.xlsx'...
  Loaded 5,000 readings across 10 turbines.
Running anomaly detection...

=================================================================
  AEROGRID — TURBINE HEALTH REPORT (24-HR SNAPSHOT)
=================================================================

Turbine       Avg Temp (°C)  Max Vib (mm/s)             Status
--------------------------------------------------------------
T-01              72.30            8.50                     OK
T-04              90.58           12.30              HIGH TEMP
T-07              74.10           25.00               HIGH VIB
...

=================================================================
  ⚠  TURBINES REQUIRING URGENT MAINTENANCE: T-04, T-07
     T-04: avg temp 90.58°C > 85.0°C
     T-07: vibration spike 25.00 mm/s > 15.0 mm/s
=================================================================
```

## Running with Docker

**Build the image**
```bash
docker build -t aerogrid-monitor .
```

**Run with your data file mounted**
```bash
docker run --rm -v /path/to/your/data:/app aerogrid-monitor
```

## Tech stack

- **Python 3.11** with pandas for data processing
- **Docker** (python:3.11-slim) for containerisation
- **Proposed cloud pipeline:** AWS Kinesis → Lambda → InfluxDB / S3 → Grafana + CloudWatch

## Architecture

The engineering report (`engineering_report.docx`) covers the full proposed pipeline architecture, including justification for each component and a cost optimisation strategy using S3 Intelligent-Tiering.
