from prefect import flow, task
import duckdb
import pandas as pd
import jsonlines
from datetime import datetime


# Constants
INPUT_FILE = "scraping_data.jsonl"
OUTPUT_DB = "property_data.db"
TABLE_NAME = "property_offers"

# Filtering Criteria
MIN_PRICE_PER_SQM = 500
MAX_PRICE_PER_SQM = 15000
VALID_PROPERTY_TYPES = {"apartment", "house"}
MIN_SCRAPING_DATE = datetime(2020, 3, 5)

@task
def extract_data(file_path):
    """Extract data from JSONL file."""
    data = []
    with jsonlines.open(file_path) as reader:
        for row in reader:
            data.append(row)
    return data

@task
def transform_data(data):
    """Transform raw data into the required format."""
    transformed_data = []
    for row in data:
        # Convert raw_price to numeric price
        raw_price = row["raw_price"].replace("€/mo.", "").replace(" ", "")
        price = float(raw_price)

        # Calculate price_per_square_meter
        living_area = row["living_area"]
        price_per_sqm = price / living_area if living_area > 0 else 0

        # Apply filtering criteria
        scraping_date = datetime.strptime(row["scraping_date"], "%Y-%m-%d")
        if (
            MIN_PRICE_PER_SQM <= price_per_sqm <= MAX_PRICE_PER_SQM
            and row["property_type"] in VALID_PROPERTY_TYPES
            and scraping_date > MIN_SCRAPING_DATE
        ):
            transformed_data.append({
                "id": row["id"],
                "scraping_date": row["scraping_date"],
                "property_type": row["property_type"],
                "municipality": row["municipality"],
                "price": price,
                "living_area": living_area,
                "price_per_square_meter": price_per_sqm,
            })
    return transformed_data

@task
def load_data(data, db_path, table_name):
    """Load transformed data into DuckDB."""
    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Connect to DuckDB and create table
    conn = duckdb.connect(db_path)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id STRING,
            scraping_date STRING,
            property_type STRING,
            municipality STRING,
            price FLOAT,
            living_area FLOAT,
            price_per_square_meter FLOAT
        )
    """)

    # Insert data into table
    conn.register('df', df)
    conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")

    # Close connection
    conn.close()

@flow
def property_pipeline():
    """Prefect flow for the property data pipeline."""
    # Step 1: Extract data
    raw_data = extract_data(INPUT_FILE)

    # Step 2: Transform data
    transformed_data = transform_data(raw_data)
    # Step 3: Load data
    load_data(transformed_data, OUTPUT_DB, TABLE_NAME)
    print(f"Data loaded into {OUTPUT_DB}.{TABLE_NAME}")

if __name__ == "__main__":
    property_pipeline()