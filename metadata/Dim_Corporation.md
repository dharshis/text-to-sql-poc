# Table: Dim_Corporation

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Entity / Ownership
* **Granularity:** One row per Ultimate Parent Company.
* **Primary Key:** `corp_id`

## Description
This table represents the top-level holding companies (e.g., Unilever, McDonald's Corp, P&G). It is used for "Company Share" calculations. Aggregating sales by `corp_id` allows for analysis of total corporate performance across all brands.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `corp_id` | INT | PK | Unique identifier for the corporation. |
| `corp_name` | VARCHAR | | The official name of the company. |
| `is_active` | BOOLEAN | | Flag indicating if the corporation is currently trading. |
| `global_headquarters` | VARCHAR | | The primary city/location of the HQ. |

## Relationships
* **References:** None (Top of hierarchy).
* **Referenced By:** `Dim_Brand.corp_id`
