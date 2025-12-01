# Table: Dim_Product_SKU

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Product Hierarchy (Level 4 - Lowest)
* **Granularity:** One row per Stock Keeping Unit (Unique Barcode).
* **Primary Key:** `sku_id`
* **Data Volume Category:** High

## 2. Table Description
This is the atomic unit of the database. Every physical item sold has a row here.

**Critical Function - Volume Normalization:**
In FMCG, you cannot simply sum "Units Sold" to get Market Volume, because 1 Unit of a 330ml can is not equal to 1 Unit of a 2L bottle.
This table contains the `volume_in_liters_kg` multiplier.
* **Formula:** `Fact_Sales.volume_sold_std` = `Fact_Sales.units_sold` * `Dim_Product_SKU.volume_in_liters_kg`.

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `sku_id` | BIGINT | **PK** | Unique identifier for the item. |
| `sku_description` | VARCHAR(255) | | Full descriptive name (e.g., 'Heineken Lager Beer Bottle 330ml'). |
| `barcode_ean` | VARCHAR(20) | | International Article Number (EAN/UPC). The code scanned at the register. |
| `subbrand_id` | INT | **FK** | Foreign Key to `Dim_SubBrand`. |
| `category_name` | VARCHAR(100) | | High-level grouping (e.g., 'Beer', 'Shampoo'). used for rough filtering before using Market Definitions. |
| `form_factor` | VARCHAR(50) | | The state of the product (e.g., 'Liquid', 'Powder', 'Bar'). Useful for manufacturing analysis. |
| `pack_type` | VARCHAR(50) | | The packaging vessel (e.g., 'Bottle', 'Can', 'Sachet'). |
| `pack_size_value` | DECIMAL(10,2) | | The labeled size (e.g., `330`). |
| `pack_size_unit` | VARCHAR(20) | | The unit on the label (e.g., `ml`, `g`). |
| `volume_in_liters_kg` | DECIMAL(10,4) | | **Normalization Factor.** Converts the pack size into a standard metric unit (Liters or KG). <br> *Example:* 330ml -> `0.3300`. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** * `Dim_SubBrand` > The line this SKU belongs to.
* **Inbound (Children):**
    * `Fact_Sales_Transactions.sku_id` > The transaction record.
    * `Bridge_Market_SKU.sku_id` > The mapping to market definitions.
