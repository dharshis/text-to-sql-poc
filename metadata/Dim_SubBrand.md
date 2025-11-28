# Table: Dim_SubBrand

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Product Hierarchy (Level 3)
* **Granularity:** One row per Brand Variant.
* **Primary Key:** `subbrand_id`

## Description
This table handles brand extensions and variants. For example, distinguishing "Dove Men+Care" from the core "Dove" brand. It is useful for deep-dive analysis into product line performance.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `subbrand_id` | INT | PK | Unique identifier for the sub-brand. |
| `subbrand_name` | VARCHAR | | The name of the specific line (e.g., "Coca-Cola Zero"). |
| `brand_id` | INT | FK | Foreign key linking to `Dim_Brand`. |

## Relationships
* **References:** `Dim_Brand` (via `brand_id`)
* **Referenced By:** `Dim_Product_SKU.subbrand_id`
