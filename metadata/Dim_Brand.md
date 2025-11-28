# Table: Dim_Brand

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Product Hierarchy (Level 2)
* **Granularity:** One row per Brand.
* **Primary Key:** `brand_id`

## Description
This table represents the major consumer-facing brands (e.g., Dove, KitKat, Budweiser). It links brands to their owning Corporation. This is the primary level for "Brand Share" reporting.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `brand_id` | INT | PK | Unique identifier for the brand. |
| `brand_name` | VARCHAR | | The name of the brand. |
| `corp_id` | INT | FK | Foreign key linking to `Dim_Corporation`. Identifies the owner. |
| `price_segment` | VARCHAR | | Strategic classification (e.g., 'Premium', 'Mass Market', 'Economy'). |

## Relationships
* **References:** `Dim_Corporation` (via `corp_id`)
* **Referenced By:** `Dim_SubBrand.brand_id`
