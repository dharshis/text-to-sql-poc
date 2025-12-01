# Table: Fact_Market_Summary

## 1. High-Level Metadata
* **Table Type:** Fact Table (Aggregate)
* **Subject Area:** Total Market Size (The Denominator)
* **Granularity:** One row per Market Definition, per Geography, per Month.
* **Primary Key:** `summary_id`
* **Data Volume Category:** Medium

## 2. Table Description
This table acts as the **Denominator** for Market Share calculations.

**The Problem it Solves:**
If you calculate Market Size by simply summing `Fact_Sales_Transactions`, you only get the size of the brands you *track*. You miss "Aldi Brand", "Local Generic Brand", etc.
This table usually comes from a syndicated data provider (Nielsen/IRI) and states the **TRUE TOTAL** of the market.

**Share Calculation Formula:**
`Share %` = `Sum(Fact_Sales_Transactions.value_sold_usd)` / `Fact_Market_Summary.total_market_value_usd`

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `summary_id` | BIGINT | **PK** | Unique row identifier. |
| `period_id` | INT | **FK** | Link to `Dim_Period`. |
| `geo_id` | INT | **FK** | Link to `Dim_Geography`. |
| `market_def_id` | INT | **FK** | Link to `Dim_Market_Definition`. Defines which "Bucket" this total represents (e.g., 'Total Hair Care'). |
| `total_market_value_usd` | DECIMAL(18,2) | | The grand total revenue of the market (tracked + untracked brands) in USD. |
| `total_market_volume_std` | DECIMAL(18,2) | | The grand total volume (Liters/KG) of the market. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** * `Dim_Period`
    * `Dim_Geography`
    * `Dim_Market_Definition`
