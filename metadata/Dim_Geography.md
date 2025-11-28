# Table: Dim_Geography

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Location / Economics
* **Granularity:** One row per Country.
* **Primary Key:** `geo_id`

## Description
This table defines the geographical scope of the data. Crucially, it handles **Multi-Currency Normalization**. It contains the exchange rates required to convert local currency sales into a standardized USD figure for global reporting.

## Column Definitions

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `geo_id` | INT | PK | Unique identifier for the location. |
| `country_name` | VARCHAR | | The full name of the country (e.g., "United Kingdom"). |
| `region_name` | VARCHAR | | The reporting region (e.g., "EMEA", "APAC", "North America"). |
| `currency_code` | CHAR(3) | | The ISO code for the local currency (e.g., "GBP", "JPY"). |
| `currency_exchange_rate` | DECIMAL | | The multiplier used to convert Local Currency to USD. (Logic: Local * Rate = USD). |

## Relationships
* **Referenced By:** `Fact_Sales_Transactions.geo_id`
* **Referenced By:** `Fact_Market_Summary.geo_id`
