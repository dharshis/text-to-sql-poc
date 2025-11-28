# Table: Fact_Sales_Transactions

## Metadata
* **Table Type:** Fact
* **Subject Area:** Sales Performance
* **Granularity:** One row per SKU, per Geography, per Period.
* **Primary Key:** `transaction_id`

## Description
This is the **Numerator** table. It stores the granular sales performance of the specific brands and SKUs tracked by the system. It contains both raw local currency values and standardized USD values. Aggregating this table provides the "Brand Sales" or "Company Sales."

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | BIGINT | PK | Unique identifier for the record. |
| `period_id` | INT | FK | Link to `Dim_Period`. |
| `geo_id` | INT | FK | Link to `Dim_Geography`. |
| `sku_id` | BIGINT | FK | Link to `Dim_Product_SKU`. |
| `units_sold` | DECIMAL | | The count of items scanned/sold. |
| `volume_sold_std` | DECIMAL | | **Volume Metric:** (`units_sold` * `sku.volume_in_liters_kg`). Used for Volume Share. |
| `value_sold_local` | DECIMAL | | Revenue in the country's origin currency. |
| `value_sold_usd` | DECIMAL | | **Value Metric:** Revenue converted to USD. Used for Value Share. |
| `is_promotion` | BOOLEAN | | Flag indicating if the sale occurred during a promo period. |
| `distribution_points`| INT | | Proxy for Weighted Distribution (how many stores sold it). |

## Relationships
* **References:** `Dim_Period`, `Dim_Geography`, `Dim_Product_SKU`
