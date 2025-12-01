# Table: Fact_Sales_Transactions

## 1. High-Level Metadata
* **Table Type:** Fact Table
* **Subject Area:** Sales Performance / POS Data
* **Granularity:** One row per SKU, per Geography, per Month.
* **Primary Key:** `transaction_id`
* **Data Volume Category:** Very High (Transactional)

## 2. Table Description
This is the core transactional table containing the **Numerator** for Market Share calculations (i.e., The Brand's Sales).
It records exactly what was sold, where, and when.

**Currency Logic:**
It stores value in BOTH Local Currency (for local country managers) and USD (for global HQ reporting), derived via the exchange rate in `Dim_Geography`.

## 3. Column Dictionary

| Column Name | Data Type | Key Type | Detailed Description & Business Logic |
| :--- | :--- | :--- | :--- |
| `transaction_id` | BIGINT | **PK** | Unique row identifier. |
| `period_id` | INT | **FK** | Link to `Dim_Period`. Identifies the month of sale. |
| `geo_id` | INT | **FK** | Link to `Dim_Geography`. Identifies the country of sale. |
| `sku_id` | BIGINT | **FK** | Link to `Dim_Product_SKU`. Identifies the exact item sold. |
| `units_sold` | DECIMAL(18,0) | | The raw count of individual items scanned/shipped. |
| `volume_sold_std` | DECIMAL(18,2) | | **Standardized Volume.** <br> *Calculation:* `units_sold` * `Dim_Product_SKU.volume_in_liters_kg`. <br> *Usage:* Used for "Volume Share" (e.g., "We own 20% of the Beer market by Volume"). |
| `value_sold_local` | DECIMAL(18,2) | | Revenue in the original currency (e.g., GBP in UK). |
| `value_sold_usd` | DECIMAL(18,2) | | **Standardized Value.** <br> *Calculation:* `value_sold_local` * `Dim_Geography.currency_exchange_rate`. <br> *Usage:* Used for "Value Share" (e.g., "We own 40% of the market by Revenue"). |
| `is_promotion` | BOOLEAN | | Flag. `True` if the sales occurred while the item was on discount/offer. Used for "Promo Efficiency" analysis. |
| `distribution_points` | INT | | A proxy metric for Weighted Distribution (0-100). Indicates availability in stores. |

## 4. Foreign Key Relationships
* **Outbound (Parent):** * `Dim_Period`
    * `Dim_Geography`
    * `Dim_Product_SKU`
