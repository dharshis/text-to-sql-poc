# Table: Dim_Period

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Time / Calendar
* **Granularity:** One row per reporting month.
* **Primary Key:** `period_id`

## Description
This table is the central time dimension for the database. It allows all sales and market data to be aligned to specific fiscal and calendar periods. It is essential for Time-Series Analysis (Year-over-Year, Quarter-over-Quarter growth).

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `period_id` | INT | PK | Unique identifier formatted as YYYYMM (e.g., 202401). Used to join to Fact tables. |
| `fiscal_year` | INT | | The financial reporting year (e.g., 2024). |
| `quarter` | INT | | The fiscal quarter (1-4). |
| `month_name` | VARCHAR | | Full text name of the month (e.g., "January"). |
| `period_type` | VARCHAR | | Indicates the scope of the period (e.g., 'Monthly', 'MAT' for Moving Annual Total). |

## Relationships
* **Referenced By:** `Fact_Sales_Transactions.period_id`
* **Referenced By:** `Fact_Market_Summary.period_id`
