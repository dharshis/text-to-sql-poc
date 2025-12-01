# Table: Dim_Brand

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Product Hierarchy (Level 2)
* **Granularity:** One row per Brand Family.
* **Primary Key:** `brand_id`
* **Data Volume Category:** Low/Medium

## 2. Table Description
The Brand Dimension represents the primary consumer-facing identity. This is the level at which Marketing Managers usually track performance (e.g., "What is KitKat's share of the Chocolate market?").

It sits between the Corporation (Owner) and the Sub-Brand (Variant).

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `brand_id` | INT | **PK** | Surrogate key for the brand. |
| `brand_name` | VARCHAR(100) | | The major brand name (e.g., 'Gatorade', 'Lays'). |
| `corp_id` | INT | **FK** | Foreign Key to `Dim_Corporation`. Links the brand to its owner. <br> *Join Logic:* `JOIN Dim_Corporation ON Dim_Brand.corp_id = Dim_Corporation.corp_id`. |
| `price_segment` | VARCHAR(50) | | Strategic tiering of the brand. <br> *Values:* 'Economy', 'Mass Market', 'Premium'. <br> *Usage:* Allows analysis of consumer down-trading during recessions. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** * `Dim_Corporation` > The owner of the brand.
* **Inbound (Children):**
    * `Dim_SubBrand.brand_id` > One Brand has Many Sub-Brands/Variants.
