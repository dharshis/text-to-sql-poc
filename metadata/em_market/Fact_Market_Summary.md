# Table: Fact_Market_Summary

## Metadata
* **Table Type:** Fact (Aggregate)
* **Subject Area:** Market Totals
* **Granularity:** One row per Market Definition, per Geography, per Period.
* **Primary Key:** `summary_id`

## Description
This is the **Denominator** table. It stores the TOTAL size of the market (Sales of tracked brands + Sales of "All Others"). It is essential for calculating accurate Market Share percentages.
* *Calculation:* `Fact_Sales_Transactions (Numerator)` / `Fact_Market_Summary (Denominator)` = Market Share %.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `summary_id` | BIGINT | PK | Unique identifier for the summary record. |
| `period_id` | INT | FK | Link to `Dim_Period`. |
| `geo_id` | INT | FK | Link to `Dim_Geography`. |
| `market_def_id` | INT | FK | Link to `Dim_Market_Definition`. |
| `total_market_value_usd`| DECIMAL | | The total revenue of the entire market category in USD. |
| `total_market_volume_std`| DECIMAL | | The total volume (Liters/Kg) of the entire market category. |

## Relationships
* **References:** `Dim_Period`, `Dim_Geography`, `Dim_Market_Definition`
