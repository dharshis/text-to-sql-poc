# Table: Dim_SubBrand

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Product Hierarchy (Level 3)
* **Granularity:** One row per Brand Line Extension / Variant.
* **Primary Key:** `subbrand_id`
* **Data Volume Category:** Medium

## 2. Table Description
Modern FMCG brands often split into distinct lines targeting different demographics or needs (e.g., 'Coke Original' vs 'Coke Zero'). The `Dim_SubBrand` table captures this granularity.

This level allows analysts to see if a brand is growing due to innovation (new sub-brands) or core performance.

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `subbrand_id` | INT | **PK** | Surrogate key for the sub-brand. |
| `subbrand_name` | VARCHAR(100) | | The specific line name (e.g., 'Dove Men+Care', 'Budweiser Zero'). |
| `brand_id` | INT | **FK** | Foreign Key to `Dim_Brand`. <br> *Join Logic:* `JOIN Dim_Brand ON Dim_SubBrand.brand_id = Dim_Brand.brand_id`. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** * `Dim_Brand` > The parent brand family.
* **Inbound (Children):**
    * `Dim_Product_SKU.subbrand_id` > One Sub-Brand has Many SKUs (different sizes/packs).
