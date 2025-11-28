# Table: Dim_Market_Definition

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Market Scope
* **Granularity:** One row per Market Definition.
* **Primary Key:** `market_def_id`

## Description
This table defines the "Universe" or "Denominator" for share calculations. Because a single product can belong to multiple analytical markets (e.g., a "KitKat" is part of the "Chocolate Market" AND the "Snack Market"), we do not hardcode categories. We use this table to create reportable groups.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `market_def_id` | INT | PK | Unique identifier for the market definition. |
| `market_name` | VARCHAR | | The analytical name (e.g., "Total Carbonated Soft Drinks"). |

## Relationships
* **Referenced By:** `Bridge_Market_SKU.market_def_id`
* **Referenced By:** `Fact_Market_Summary.market_def_id`
