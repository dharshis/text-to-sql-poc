# Table: Dim_Period

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Temporal / Calendar / Fiscal Reporting
* **Granularity:** One row per specific reporting month (e.g., January 2024).
* **Primary Key:** `period_id`
* **Data Volume Category:** Low (Static)

## 2. Table Description
This table acts as the central temporal anchor for the Data Warehouse. Unlike a standard calendar date table, this table is aggregated to the **Monthly** level, which is the standard granularity for FMCG/Market Share reporting (Nielsen/IRI standard).

It supports both **Calendar Years** and **Fiscal Years**, allowing financial reporting alignment. All Fact tables (`Fact_Sales_Transactions`, `Fact_Market_Summary`) must join to this table to enable Time-Series Analysis (YTD, MAT, YoY).

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `period_id` | INT | **PK** | The unique identifier for the time bucket. **Format:** `YYYYMM` (Integer). <br> *Example:* `202401` for January 2024. <br> *Usage:* Optimized for integer-based joins and sorting. Do not treat as a date type directly. |
| `fiscal_year` | INT | | The financial year the month belongs to. Useful for companies whose fiscal year does not match the calendar year (e.g., starts in April). |
| `quarter` | INT | | The quarter of the year (1, 2, 3, or 4). Used for Quarterly Business Reviews (QBR). |
| `month_name` | VARCHAR(20) | | The descriptive English name of the month (e.g., 'January'). Used for label display in BI dashboards. |
| `period_type` | VARCHAR(20) | | Describes the nature of the period. <br> *Values:* 'Monthly'. <br> *Future Extensibility:* Can include '4-Week' or 'Weekly' if granularity changes. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** None.
* **Inbound (Children):**
    * `Fact_Sales_Transactions.period_id` > Links sales data to time.
    * `Fact_Market_Summary.period_id` > Links market totals to time.
