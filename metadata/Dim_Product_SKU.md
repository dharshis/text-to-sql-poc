# Table: Dim_Product_SKU

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Product Hierarchy (Level 4 - Lowest)
* **Granularity:** One row per unique Stock Keeping Unit (Item).
* **Primary Key:** `sku_id`

## Description
This is the most critical dimension for FMCG analysis. It defines the physical attributes of the product. It contains the normalization factors (`volume_in_liters_kg`) that allow distinct products (e.g., a Shampoo Bottle vs. a Burger) to be aggregated into a standard "Market Volume."

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `sku_id` | BIGINT | PK | Unique identifier for the specific item. |
| `sku_description` | VARCHAR | | Full product name (e.g., "Dove Shampoo Daily Moisture 400ml"). |
| `barcode_ean` | VARCHAR | | The EAN/UPC barcode scanned at point of sale. |
| `subbrand_id` | INT | FK | Foreign key linking to `Dim_SubBrand`. |
| `category_name` | VARCHAR | | The broad category (e.g., "Hair Care", "Fast Food"). |
| `form_factor` | VARCHAR | | The physical state (e.g., 'Liquid', 'Solid', 'Powder'). |
| `pack_type` | VARCHAR | | Packaging style (e.g., 'Bottle', 'Can', 'Wrapper'). |
| `pack_size_value` | DECIMAL | | The numeric size (e.g., 400). |
| `pack_size_unit` | VARCHAR | | The unit of measure (e.g., 'ml', 'g'). |
| `volume_in_liters_kg`| DECIMAL | | **Critical Metric:** Standardized volume conversion factor. (e.g., 400ml = 0.4). Used to calculate Volume Share. |

## Relationships
* **References:** `Dim_SubBrand` (via `subbrand_id`)
* **Referenced By:** `Fact_Sales_Transactions.sku_id`
* **Referenced By:** `Bridge_Market_SKU.sku_id`
