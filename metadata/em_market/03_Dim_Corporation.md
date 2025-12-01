# Table: Dim_Corporation

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Corporate Hierarchy (Level 1 - Top)
* **Granularity:** One row per Ultimate Parent Corporation.
* **Primary Key:** `corp_id`
* **Data Volume Category:** Low

## 2. Table Description
This table represents the highest level of the competitive hierarchy. It answers the question: "Who ultimately owns this brand?"

This is essential for **Company Share** reporting. For example, 'Dove', 'Axe', and 'Hellmanns' are distinct brands, but their sales must roll up to 'Unilever' (Level 1) to calculate Unilever's total share of wallet vs. P&G.

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `corp_id` | INT | **PK** | Surrogate key for the corporation. |
| `corp_name` | VARCHAR(100) | | The legal entity name (e.g., 'Procter & Gamble', 'Nestlé'). |
| `is_active` | BOOLEAN | | Logic flag. `True` means the company is currently active. `False` implies bankruptcy or acquisition. |
| `global_headquarters` | VARCHAR(100) | | City/Country of the global HQ. Useful for regional bias analysis. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** None.
* **Inbound (Children):**
    * `Dim_Brand.corp_id` > One Corporation owns Many Brands.
