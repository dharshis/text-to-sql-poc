# Table: Dim_Geography

## 1. High-Level Metadata
* **Table Type:** Dimension
* **Subject Area:** Location / Macro-Economics
* **Granularity:** One row per Country.
* **Primary Key:** `geo_id`
* **Data Volume Category:** Low (Static)

## 2. Table Description
This table defines the physical markets where products are sold. Its most critical function is acting as the **Currency Conversion Hub**.

FMCG reporting requires two views:
1.  **Local View:** How much did we sell in Japan (in Yen)?
2.  **Global View:** How much did we sell globally (standardized to USD)?

This table stores the `currency_exchange_rate` used to convert Fact table local values into USD values during ETL or View generation.

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `geo_id` | INT | **PK** | Surrogate key uniquely identifying a country market. |
| `country_name` | VARCHAR(100) | | The standard reporting name of the country (e.g., 'United Kingdom'). |
| `region_name` | VARCHAR(100) | | The super-region for high-level aggregation. <br> *Examples:* 'APAC' (Asia Pacific), 'EMEA' (Europe, Middle East, Africa), 'LATAM' (Latin America), 'NA' (North America). |
| `currency_code` | CHAR(3) | | The ISO 4217 currency code used in that country (e.g., 'GBP', 'EUR', 'JPY'). |
| `currency_exchange_rate` | DECIMAL(10,6) | | The conversion factor to USD. <br> *Formula:* `Value_Local` * `currency_exchange_rate` = `Value_USD`. <br> *Note:* In a production system, this might be snapshot-based, but for this model, it is a fixed reference rate. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** None.
* **Inbound (Children):**
    * `Fact_Sales_Transactions.geo_id` > Defines where the transaction occurred.
    * `Fact_Market_Summary.geo_id` > Defines the location of the total market size.
