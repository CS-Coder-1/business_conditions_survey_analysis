import sys
from pathlib import Path

import pandas as pd
import altair as alt


# Configuration

COMBINED_FILE = Path("combined_business_conditions.csv")
OUTPUT_FILE = Path("net_expectation.html")


# Get new quarterly file

if len(sys.argv) != 2:
    raise ValueError(
        "Usage: python pipeline.py <new_quarterly_csv>"
    )

INPUT_FILE = Path(sys.argv[1])

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE.resolve()}"
    )

print(f"Input file: {INPUT_FILE.resolve()}")


# Read new quarterly file

new_data = pd.read_csv(INPUT_FILE)

print(f"Rows in new file: {len(new_data)}")


# Standardize column names

new_data.columns = (
    new_data.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)


# Validate required schema

required_columns = {
    "geo",
    "business_characteristics",
    "business_information",
    "expected_change",
    "value",
    "quarter"
}

missing_columns = required_columns - set(new_data.columns)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

print("Schema validation passed.")


# Clean text fields

text_columns = new_data.select_dtypes(
    include=["object", "string"]
).columns

for col in text_columns:
    new_data[col] = new_data[col].str.strip()


# Standardize expected-change labels
new_data["expected_change"] = (
    new_data["expected_change"]
    .str.lower()
    .replace({
        "stay about the same": "stay the same"
    })
)


# Standardize business-information labels
new_data["business_information"] = (
    new_data["business_information"]
    .replace({
        "Capital Investment": "Investment"
    })
)


# Convert VALUE to numeric
new_data["value"] = pd.to_numeric(
    new_data["value"],
    errors="coerce"
)


#Validate expected-change categories
expected_categories = {
    "increase",
    "stay the same",
    "decrease"
}

observed_categories = set(
    new_data["expected_change"].dropna().unique()
)

unexpected_categories = (
    observed_categories - expected_categories
)

if unexpected_categories:
    raise ValueError(
        "Unexpected Expected_change categories: "
        f"{sorted(unexpected_categories)}"
    )

print("Expected-change category validation passed.")


# Validate VALUE range

invalid_values = new_data[
    (new_data["value"] < 0) |
    (new_data["value"] > 100)
]

if len(invalid_values) > 0:
    raise ValueError(
        f"Found {len(invalid_values)} values outside "
        "the 0-100 range."
    )

print("VALUE range validation passed.")


# Validate quarter field

quarter_values = new_data["quarter"].dropna().unique()

if len(quarter_values) != 1:
    raise ValueError(
        "The new input file must contain exactly one quarter. "
        f"Found: {list(quarter_values)}"
    )

new_quarter = quarter_values[0]

print(f"Quarter being ingested: {new_quarter}")


# Check duplicate analytical records within new file

key_columns = [
    "geo",
    "business_characteristics",
    "business_information",
    "expected_change",
    "quarter"
]

duplicate_keys = (
    new_data
    .groupby(key_columns)
    .size()
    .reset_index(name="count")
)

duplicate_keys = duplicate_keys[
    duplicate_keys["count"] > 1
]

if len(duplicate_keys) > 0:
    raise ValueError(
        "Duplicate analytical records detected in the "
        "new quarterly file."
    )

print("Duplicate-key validation passed.")


# Load existing combined dataset

if COMBINED_FILE.exists():

    combined = pd.read_csv(COMBINED_FILE)

    combined.columns = (
        combined.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    print(
        f"Existing combined dataset found: "
        f"{len(combined)} rows"
    )

else:

    combined = pd.DataFrame(
        columns=new_data.columns
    )

    print(
        "No combined dataset found. "
        "A new combined dataset will be created."
    )

# Validate combined dataset schema

combined_missing_columns = (
    required_columns - set(combined.columns)
)

if combined_missing_columns:
    raise ValueError(
        "Existing combined dataset is missing required "
        f"columns: {sorted(combined_missing_columns)}"
    )


# Append new quarter

combined = pd.concat(
    [
        combined,
        new_data
    ],
    ignore_index=True
)


# Remove exact duplicate records

rows_before = len(combined)

combined = combined.drop_duplicates()

duplicates_removed = (
    rows_before - len(combined)
)

print(
    f"Exact duplicate rows removed: "
    f"{duplicates_removed}"
)


# Save updated combined dataset

combined.to_csv(
    COMBINED_FILE,
    index=False
)

print(
    f"Combined dataset saved to: "
    f"{COMBINED_FILE.resolve()}"
)


# Create national all-industry dataset

all_industries = (
    "North American Industry Classification System (NAICS), all industries"
)

national_all_industry = combined[
    (combined["geo"] == "Canada") &
    (
        combined["business_characteristics"]
        == all_industries
    )
].copy()


print(
    "National all-industry observations:",
    len(national_all_industry)
)


# Calculate Net Expectation

net_expectation = (
    national_all_industry
    .pivot(
        index=[
            "quarter",
            "business_information"
        ],
        columns="expected_change",
        values="value"
    )
    .reset_index()
)

net_expectation.columns.name = None


# Net expectation is only available when both increase
# and decrease values are present.
net_expectation["net_expectation"] = (
    net_expectation["increase"]
    - net_expectation["decrease"]
)

# Create Altair chart

net_chart = (

    alt.Chart(net_expectation)

    .mark_line(point=True)

    .encode(

        x=alt.X(
            "quarter:N",
            sort=[
                "Q3 2023",
                "Q4 2023",
                "Q1 2024",
                "Q2 2024"
            ],
            title="Quarter"
        ),

        y=alt.Y(
            "net_expectation:Q",
            title="Net expectation (percentage points)"
        ),

        color=alt.Color(
            "business_information:N",
            title="Business metric"
        ),

        tooltip=[

            alt.Tooltip(
                "quarter:N",
                title="Quarter"
            ),

            alt.Tooltip(
                "business_information:N",
                title="Business metric"
            ),

            alt.Tooltip(
                "net_expectation:Q",
                title="Net expectation",
                format=".1f"
            )
        ]

    )

    .properties(
        title="Net Business Expectations Over Time",
        width=700,
        height=400
    )
)


# Save chart

net_chart.save(OUTPUT_FILE)

print(
    f"Chart saved to: {OUTPUT_FILE.resolve()}"
)

print("\nPipeline completed successfully.")