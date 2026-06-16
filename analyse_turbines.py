"""
AeroGrid Turbine Anomaly Detection Service

Parses 24-hour IoT telemetry data from offshore wind turbines
and flags any turbine requiring urgent maintenance.

Anomaly Rules:
  - if Avg Temp > 85.0°C
  - Any vibration reading > 15.0 mm/s

How to run:
  1. Install dependencies:
       py -m pip install pandas openpyxl
  2. Place telemetry_data.xlsx in the same directory as this script.
  3. Run:
       python analyse_turbines.py

Output:
  Prints a summary table and a final list of turbines requiring maintenance.
"""

import pandas as pd
import sys

# These are the settings that decide when a turbine is flagged as problematic.
# If the average temperature goes above 85°C, or if vibration ever spikes above
# 15 mm/s at any point during the day, that turbine gets marked for maintenance.
DATA_FILE = "telemetry_data.xlsx"
TEMP_THRESHOLD = 85.0    # °C  — temperature threshold
VIB_THRESHOLD  = 15.0    # mm/s — vibration threshold


def load_data(filepath: str) -> pd.DataFrame:
    """Load telemetry data from an Excel file into a DataFrame."""

    # Try to open the Excel file. If it's not there, tell the user and stop
    # the program — there's nothing useful we can do without the data.
    try:
        df = pd.read_excel(filepath)
    except FileNotFoundError:
        print(f"ERROR: Could not find '{filepath}'. "
              "Make sure it is in the same directory as this script.")
        sys.exit(1)

    # Check that the file has the three columns we actually need.
    # If someone hands us a different spreadsheet by accident, we catch it here
    # rather than crashing with a confusing error later on.
    required_cols = {"turbine_id", "temperature_c", "vibration_mm_s"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"ERROR: Missing expected columns: {missing}")
        sys.exit(1)

    return df


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-turbine metrics and apply anomaly rules.

    Returns a DataFrame with one row per turbine containing:
      - avg_temp_c      : mean temperature across all readings
      - max_vibration   : highest single vibration reading
      - temp_alert      : True if avg temp exceeds threshold
      - vib_alert       : True if any vibration spike exceeds threshold
      - needs_maintenance: True if either alert is triggered
    """

    # The raw data has one row per sensor reading, so there can be hundreds of
    # rows for each turbine. Here we collapse all of those down to a single
    # summary row per turbine, keeping only what we care about:
    #   - the average temperature across the whole day
    #   - the single worst vibration spike seen at any point
    #   - a count of how many readings we got (useful for sanity-checking)
    stats = df.groupby("turbine_id").agg(
        avg_temp_c    =("temperature_c",   "mean"),
        max_vibration =("vibration_mm_s",  "max"),
        reading_count =("temperature_c",   "count"),
    ).round(2)

    # Now apply the two rules. Each of these adds a True/False column:
    #   temp_alert  — did the average temperature run too hot?
    #   vib_alert   — did vibration hit a dangerous spike at any point?
    # A turbine needs maintenance if it tripped either rule, hence the OR (|).
    stats["temp_alert"]        = stats["avg_temp_c"]   > TEMP_THRESHOLD
    stats["vib_alert"]         = stats["max_vibration"] > VIB_THRESHOLD
    stats["needs_maintenance"] = stats["temp_alert"] | stats["vib_alert"]

    return stats


def print_report(stats: pd.DataFrame) -> None:
    """Print a clear summary table and the final maintenance list."""

    # Print the header row of the table, with each column right-aligned so the
    # numbers line up neatly underneath.
    print("\n" + "=" * 65)
    print("  AEROGRID — TURBINE HEALTH REPORT (24-HR SNAPSHOT)")
    print("=" * 65)
    print(f"\n{'Turbine':<10} {'Avg Temp (°C)':>14} {'Max Vib (mm/s)':>15} {'Status':>18}")
    print("-" * 62)

    # Go through each turbine one by one (sorted alphabetically so the output
    # is consistent every time) and print its numbers plus a plain-English status.
    for turbine_id, row in stats.sort_index().iterrows():
        flags = []
        if row["temp_alert"]:
            flags.append("HIGH TEMP")
        if row["vib_alert"]:
            flags.append("HIGH VIB")
        # If neither flag fired, the turbine is fine — just show "OK".
        status = ", ".join(flags) if flags else "OK"
        print(f"{turbine_id:<10} {row['avg_temp_c']:>14.2f} {row['max_vibration']:>15.2f} {status:>18}")

    # Pull out just the turbine IDs that need attention so we can list them
    # clearly at the bottom of the report, along with the specific reason why.
    failing = stats[stats["needs_maintenance"]].index.tolist()

    print("\n" + "=" * 65)
    if failing:
        print(f"  ⚠  TURBINES REQUIRING URGENT MAINTENANCE: {', '.join(sorted(failing))}")
        # For each flagged turbine, spell out exactly which threshold it broke
        # and by how much — gives the maintenance team what they need at a glance.
        for t in sorted(failing):
            row = stats.loc[t]
            reasons = []
            if row["temp_alert"]:
                reasons.append(f"avg temp {row['avg_temp_c']:.2f}°C > {TEMP_THRESHOLD}°C")
            if row["vib_alert"]:
                reasons.append(f"vibration spike {row['max_vibration']:.2f} mm/s > {VIB_THRESHOLD} mm/s")
            print(f"     {t}: {'; '.join(reasons)}")
    else:
        print("  ✓  All turbines are operating within normal parameters.")
    print("=" * 65 + "\n")


def main():
    # Wrap everything in a top-level try/except so that any unexpected runtime
    # error (a corrupt row in the spreadsheet, a pandas version mismatch, etc.)
    # surfaces as a clean message rather than a raw Python traceback — much more
    # useful for the on-call engineer running this in production.
    try:
        # Step 1: load the spreadsheet.
        print(f"Loading data from '{DATA_FILE}'...")
        df = load_data(DATA_FILE)
        print(f"  Loaded {len(df):,} readings across {df['turbine_id'].nunique()} turbines.")

        # Step 2: crunch the numbers and flag anything out of range.
        print("Running anomaly detection...")
        stats = detect_anomalies(df)

        # Step 3: print the final report to the terminal.
        print_report(stats)

    except Exception as exc:
        # Anything that slipped past the specific checks above lands here.
        # We print the error type and message so the cause is obvious, then
        # exit with a non-zero code so CI/CD pipelines can detect the failure.
        print(f"ERROR: Unexpected failure — {type(exc).__name__}: {exc}")
        sys.exit(1)


# This block makes sure main() only runs when you execute this file directly.
# If another script were to import this one, main() wouldn't fire automatically.
if __name__ == "__main__":
    main()
