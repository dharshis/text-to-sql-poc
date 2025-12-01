# Table: Bridge_Market_SKU

## 1. High-Level Metadata
* **Table Type:** Bridge (Junction Table)
* **Subject Area:** Market Scope Mapping
* **Granularity:** Unique combination of Market Definition + SKU.
* **Primary Key:** Composite (`market_def_id`, `sku_id`)
* **Data Volume Category:** High

## 2. Table Description
This table resolves the **Many-to-Many relationship** between Products and Markets.
1.  One SKU (e.g., "Coke Zero") can belong to multiple Markets ("Soft Drinks Market" AND "Low Calorie Beverage Market").
2.  One Market ("Soft Drinks") contains multiple SKUs.

**Query Logic:**
To find all products in the "Soft Drink Market":
`JOIN Bridge_Market_SKU ON Dim_Market_Definition.id = Bridge.market_id JOIN Dim_Product_SKU ON Bridge.sku_id = Dim_Product_SKU.id`

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `market_def_id` | INT | **PK/FK** | Link to `Dim_Market_Definition`. |
| `sku_id` | BIGINT | **PK/FK** | Link to `Dim_Product_SKU`. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** * `Dim_Market_Definition`
    * `Dim_Product_SKU`
