# Table: Bridge_Market_SKU

## Metadata
* **Table Type:** Bridge / Junction
* **Subject Area:** Market Scope Mapping
* **Granularity:** Unique combination of Market Definition and SKU.
* **Primary Key:** Composite (`market_def_id`, `sku_id`)

## Description
This table implements a **Many-to-Many** relationship between Products (SKUs) and Markets. It allows the system to flexibly include or exclude SKUs from specific market definitions without altering the product table.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `market_def_id` | INT | FK | Link to the Market Definition. |
| `sku_id` | BIGINT | FK | Link to the specific SKU. |

## Relationships
* **References:** `Dim_Market_Definition`
* **References:** `Dim_Product_SKU`
