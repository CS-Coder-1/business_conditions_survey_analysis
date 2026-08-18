# Business Data Lab: Business Conditions Survey

## Overview

This project analyzes four quarterly Business Conditions Survey files covering Q3 2023 through Q2 2024.

The project contains two analytical components:

1. **Part 1: Analysis**

   * National business expectations over time using a Net Expectation measure.
   * Provincial employment expectations for Q2 2024.
   * Data quality and validation checks.

2. **Part 2: Ingestion and Presentation Pipeline**

   * Accepts a new quarterly CSV file.
   * Validates and standardizes the incoming data.
   * Appends the new quarter to the historical combined dataset.
   * Regenerates the national Net Expectation chart.

The analysis was completed in Python using pandas and Altair.

---

# Project Structure

```text
business_data_lab_assignment_project/
│
├── Data_CSBC-Q3_2023.csv
├── Data_CSBC-Q4_2023.csv
├── Data_CSBC-Q1_2024.csv
├── Data_CSBC-Q2_2024.csv
├── Data_CSBC-Q3_2024_test.csv
│
├── business_conditions_analysis.ipynb
├── pipeline.py
├── combined_business_conditions.csv
├── net_expectation.html
│
├── outputs/
│   ├── net_expectation.png
│   └── provincial_employment.png
│
├── requirements.txt
└── README.md
```

The exact files included may vary depending on the submission format. The Q3 2024 test file is included only to demonstrate that the pipeline can ingest a future quarterly file.

---

# Part 1: Analysis

## Data Preparation

The four quarterly files were loaded and combined into a single dataset.

Before analysis, the data was cleaned by:

* Standardizing column names to lowercase with underscores.
* Removing leading and trailing whitespace from text fields.
* Standardizing expected-change labels such as `"stay about the same"` to `"stay the same"`.
* Converting `VALUE` to numeric.
* Standardizing the business-information label for investment where necessary.

The national analysis uses:

> **Canada and North American Industry Classification System (NAICS), all industries**

This provides a consistent population for comparing the four quarters.

---

## Data Quality Checks

Several validation checks were performed before analysis.

### Missing values

Missing values were inspected in each source file and again after combining the quarterly datasets.

### Percentage range

Because `VALUE` represents a percentage, observations were checked to ensure that values fell between 0 and 100.

### Expected-change categories

The expected categories were checked against:

```text
increase
stay the same
decrease
```

Unexpected category labels would be flagged rather than silently incorporated.

### Three-way percentage split

For each combination of:

```text
GEO
Business_characteristics
Business_information
Quarter
```

the three expected-change percentages were summed and compared with 100%.

A tolerance of plus or minus 1 percentage point was used to account for rounding.

### Q2 2024 missing values

A notable data quality issue was identified in the national all-industry Q2 2024 data. The `decrease` values for Employment, Sales, Profitability, and Investment are missing.

These values were intentionally **not replaced with zero**. A missing value does not imply that zero businesses expected a decrease, and replacing the values with zero would create unsupported results.

Consequently, Q2 2024 national Net Expectation values are left as unavailable.

---

# Analysis 1: Net Expectation

Net Expectation is defined as:

```text
Net Expectation = % expecting an increase - % expecting a decrease
```

A positive value indicates that more businesses expect an increase than a decrease. A negative value indicates that the opposite is true.

The analysis compares Net Expectation across:

* Employment
* Sales
* Profitability
* Investment

for the available quarters.

The visualization is a line chart showing how expectations changed over time.

### Interpretation

Net expectation provides a simple measure of whether business expectations are tilted toward improvement or deterioration. Positive values indicate that a larger share of businesses expect an increase than a decrease, while negative values indicate the opposite. The chart allows changes in expectations across Employment, Sales, Profitability, and Investment to be compared over time. Q2 2024 is not included in the national Net Expectation comparison because the source data contains missing `decrease` percentages for all four measures. These values were not treated as zero because doing so would introduce an unsupported assumption. Overall, the available data shows that Net Expectations for the four business metrics decreased in Q4 2023 before rebounding in Q1 2024.

---

# Analysis 2: Provincial Employment Expectations

The second analysis focuses on Employment expectations in Q2 2024.

The Canada aggregate is removed so that individual provinces can be compared directly.

For each province, Net Employment Expectation is calculated as:

```text
% expecting employment to increase
-
% expecting employment to decrease
```

The results are displayed as a horizontal bar chart, with tooltips showing the underlying increase, stay-the-same, decrease, and Net Expectation percentages.

### Interpretation

Employment expectations vary across provinces, with the Net Expectation showing the balance between businesses expecting employment to increase and those expecting it to decrease. Provinces with higher positive Net Expectations have a stronger balance of businesses anticipating employment growth. This comparison provides a useful snapshot of geographic differences in near-term employment expectations. In Q2 2024, the Northwest Territories and Prince Edward Island had the highest positive employment Net Expectations in the dataset. These results should be interpreted as business expectations rather than forecasts of actual employment changes.

---

# Part 2: Ingestion and Presentation Pipeline

## What the Pipeline Does

`pipeline.py` accepts a new quarterly CSV file and:

1. Reads the incoming file.
2. Standardizes column names.
3. Cleans text fields and known category labels.
4. Validates the required schema.
5. Checks expected-change categories.
6. Checks that percentage values are within 0 to 100.
7. Verifies that the input contains one quarter.
8. Checks for duplicate analytical records.
9. Loads the existing combined dataset, if present.
10. Appends the new quarter.
11. Removes exact duplicate records.
12. Saves the updated combined dataset.
13. Recalculates national all-industry Net Expectation.
14. Regenerates the Net Expectation chart as an HTML file.

This allows a future quarterly file to be incorporated without manually editing the analysis code.

---

## Running the Pipeline

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python pipeline.py <new_quarterly_csv>
```

For example:

```bash
python pipeline.py Data_CSBC-Q3_2024_test.csv
```

The pipeline will update:

```text
combined_business_conditions.csv
```

and generate:

```text
net_expectation.html
```

The HTML file can be opened in a web browser to view the refreshed Altair visualization.

---

## Expected Input Format

The incoming quarterly CSV is expected to contain the following fields:

```text
GEO
Business_characteristics
Business_information
Expected_change
VALUE
Quarter
```

The `Quarter` field should contain the quarter represented by the new file, such as:

```text
Q3 2024
```

The same general schema and category structure as the historical files are expected.

---

## Potential Future Breaks

One potential issue is **schema drift**. For example, a future file could rename a column, remove a required field, or introduce a new category value.

The pipeline explicitly validates the required columns and expected-change categories and raises an error when an unexpected structure is detected. In a production environment, the validation could be extended to compare row counts, category frequencies, and other structural characteristics with previous quarters and flag unexpected changes for review.

Another possible issue is missing values in future quarters. The pipeline preserves missing values rather than automatically treating them as zero, avoiding unsupported assumptions in downstream calculations.

---

# Assumptions and Limitations

* `VALUE` is interpreted as a percentage from 0 to 100.
* Increase, stay-the-same, and decrease are treated as the survey's expected-change categories.
* A plus or minus 1 percentage point tolerance is used when checking whether the three categories approximately sum to 100.
* Net Expectation is calculated as increase minus decrease.
* Missing values are not imputed.
* The national analysis uses Canada and the all-industries NAICS grouping.
* The provincial analysis excludes the Canada aggregate.
* Net Expectation describes business expectations and should not be interpreted as a forecast of realized economic outcomes.
* The analysis is descriptive and does not attempt to establish causal relationships between business expectations and economic conditions.

---

# Dependencies

The project uses:

```text
pandas
numpy
altair
```

Install them with:

```bash
pip install -r requirements.txt
```

---

# Reproducibility

To reproduce the Part 1 analysis, open:

```text
business_conditions_analysis.ipynb
```

and run the notebook from top to bottom.

To test the recurring quarterly ingestion workflow, provide a new quarterly CSV to:

```text
pipeline.py
```

using the command:

```bash
python pipeline.py <new_quarterly_csv>
```
