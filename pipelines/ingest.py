"""
Stage 1: Data Ingestion
-----------------------
Copies the raw dataset from data/raw/ to data/processed/ingested.csv
Validates file existence and basic integrity (non-empty, has rows).
"""

import os
import sys
import shutil
import logging
import yaml
import pandas as pd

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("ingest")


def load_params():
    """Load pipeline parameters from params.yaml."""
    try:
        with open("params.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("params.yaml not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing params.yaml: {e}")
        sys.exit(1)


def main():
    logger.info("Starting data ingestion...")
    params = load_params()
    
    try:
        raw_path = params["data"]["raw_path"]
        processed_dir = params["data"]["processed_dir"]
    except KeyError as e:
        logger.error(f"Missing required parameter in params.yaml: {e}")
        sys.exit(1)

    output_path = os.path.join(processed_dir, "ingested.csv")

    # --- Validate source file exists ---
    if not os.path.exists(raw_path):
        logger.error(f"Raw data file not found: {raw_path}")
        sys.exit(1)

    # --- Validate file is non-empty ---
    file_size = os.path.getsize(raw_path)
    if file_size == 0:
        logger.error(f"Raw data file is empty: {raw_path}")
        sys.exit(1)

    # --- Load and validate row count ---
    try:
        # STRICT: Memory Safety. 
        # Do not load entire dataset just to check if it's empty.
        # Check first few rows to validate format, then use file size/metadata if possible.
        # Ensure engine is 'c' for speed and strict evaluation.
        df_sample = pd.read_csv(raw_path, nrows=5, engine="c")
    except Exception as e:
        logger.error(f"Failed to read CSV format correctly: {e}")
        sys.exit(1)

    if len(df_sample) == 0:
        logger.error(f"Raw data file has no data rows: {raw_path}")
        sys.exit(1)

    # --- Ensure output directory exists ---
    os.makedirs(processed_dir, exist_ok=True)

    # --- Copy to processed ---
    try:
        shutil.copy2(raw_path, output_path)
    except IOError as e:
        logger.error(f"Failed to copy file: {e}")
        sys.exit(1)
    logger.info(f"Ingestion complete: Sample of {len(df_sample)} rows checked from {raw_path}")
    logger.info(f"Data successfully copied to {output_path}")
    logger.info(f"File size: {file_size:,} bytes")
    logger.info(f"Columns: {list(df_sample.columns)}")


if __name__ == "__main__":
    main()
