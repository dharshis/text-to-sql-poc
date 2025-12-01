# Table: Dim_Market_Definition

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Market Scope / Reporting Definitions
* **Granularity:** One row per Market Definition.
* **Primary Key:** `market_def_id`
* **Data Volume Category:** Low

## 2. Table Description
Market definitions in FMCG are fluid. A "Market" is a collection of SKUs that compete with each other.
* *Example:* A "Quick Lunch Market" might include Burgers (Food) AND Ready-to-Drink Coffee (Beverage).

This table defines those "Buckets". It is the **Denominator** entity for Market Share calculations.

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `market_def_id` | INT | **PK** | Unique identifier for the market scope. |
| `market_name` | VARCHAR(100) | | The reporting name (e.g., 'Total Carbonated Soft Drinks', 'Wet Shampoos'). |

## 4. Foreign Key Relationships
* **Outbound (Parent):** None.
* **Inbound (Children):**
    * `Bridge_Market_SKU.market_def_id` > Maps SKUs to this definition.
    * `Fact_Market_Summary.market_def_id` > Stores the total size of this market.
