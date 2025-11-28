# Client Demo Script - Text-to-SQL with Agentic AI

**Date:** November 27, 2025  
**Architect:** Winston  
**Purpose:** Showcase agentic capabilities with market research data

---

## Demo Setup

**URL:** http://localhost:5173  
**Active Dataset:** Market Size Analytics  
**Clients Available:** 
- Acme Corporation (Manufacturing, Enterprise)
- GlobalTech Industries (Technology, Professional)
- MegaRetail Group (Retail, Enterprise)

**Available Data:**
- **Markets:** Electric Vehicles, EV Batteries, EV Charging Infrastructure, Automotive, and 8 more
- **Countries:** World, China, USA, India, Norway, and 20+ more
- **Years:** 2023, 2024, 2025 (actual) + 2026 (forecasts)
- **Emerging Markets:** India, Brazil, Mexico, Indonesia, Thailand, Vietnam, South Africa

---

## Part 1: Core Analytics Queries (Work Out of the Box)

### Query 1: Top Markets by Value
**User:** "Show me the top 5 electric vehicle markets in 2025"

**Expected:**
- ✅ Returns 5 countries ranked by market value
- Shows China, USA, India, Norway, etc.
- Values in millions USD

**Showcases:** Basic SQL generation, aggregation, sorting

---

### Query 2: Quarterly Trends
**User:** "What's the quarterly trend for EV batteries in China in 2025?"

**Expected:**
- ✅ Returns Q1-Q4 data for China
- Shows EV Batteries market specifically
- Quarterly aggregation

**Showcases:** Time-series analysis, specific market + country filtering

---

### Query 3: Country Comparison
**User:** "Compare electric vehicle market size between USA and China in 2025"

**Expected:**
- ✅ Returns side-by-side comparison
- Shows both countries' EV market values
- Clear comparison format

**Showcases:** Multi-entity comparison, filtering

---

### Query 4: Emerging Markets Analysis
**User:** "Which emerging markets have the highest EV growth forecast?"

**Expected:**
- ✅ Returns India, Brazil, Mexico, Thailand, Vietnam, Indonesia, South Africa
- Shows forecast data for 2026
- Ranked by growth/CAGR

**Showcases:** Dimension filtering (is_emerging_market), forecasts

---

### Query 5: Currency Analysis
**User:** "Show me electric vehicle market value in constant USD"

**Expected:**
- ✅ Returns EV data in USD-CON currency
- Inflation-adjusted values
- Comparison with current USD possible

**Showcases:** Currency dimension, inflation adjustment

---

### Query 6: Year-over-Year Growth
**User:** "What's the year-over-year growth rate for electric vehicles from 2024 to 2025?"

**Expected:**
- ✅ Returns growth percentage
- Compares 2024 vs 2025 values
- Shows calculation

**Showcases:** Temporal comparison, calculated metrics

---

### Query 7: Market Breakdown
**User:** "Show me the EV ecosystem breakdown - batteries, charging, motors, and vehicles"

**Expected:**
- ✅ Returns 4 market segments
- EV Batteries, EV Charging Infrastructure, Electric Motors, Electric Vehicles
- Market values for each

**Showcases:** Multi-market aggregation, market ecosystem view

---

### Query 8: Forecast Scenarios
**User:** "Compare base case vs optimistic forecast for electric vehicles in 2026"

**Expected:**
- ✅ Returns 2 scenarios side by side
- Base Case and Optimistic forecasts
- Shows variance between scenarios

**Showcases:** Scenario analysis, forecast data

---

### Query 9: Regional Distribution
**User:** "What's the market concentration - do top 3 countries dominate electric vehicles?"

**Expected:**
- ✅ Returns top 3 countries with % share
- Shows China, USA, and #3 country
- Calculates market concentration percentage

**Showcases:** Market concentration analysis, percentage calculations

---

### Query 10: Multi-Market Comparison
**User:** "Show me the top 5 markets by value in 2025 - any market type"

**Expected:**
- ✅ Returns top 5 across ALL markets (not just EV)
- Could be EV Batteries, Electric Vehicles, Automotive, etc.
- Sorted by total value

**Showcases:** Cross-market analysis, global aggregation

---

## Part 2: Clarification Scenarios (Showcases AI Intelligence)

### Scenario A: Ambiguous Entity
**User:** "Show me the trends"

**Expected:**
- ❓ Asks clarification: "What market are you interested in? (Electric Vehicles, EV Batteries, Automotive?)"
- ❓ Asks: "Which time period?"

**Showcases:** Detects missing entity and time period

---

### Scenario B: Vague Location
**User:** "How about Asia?"

**Expected:**
- ❓ Asks: "What would you like to know about Asia?"
- ❓ Suggests: "Examples: 'EV market value in Asia', 'Asia Pacific market trends'"

**Showcases:** Detects incomplete context, helpful suggestions

---

### Scenario C: Fragment Query
**User:** "by region"

**Expected:**
- ❓ Asks: "What data would you like to see?"
- ❓ Asks: "What metric? (market value, volume, growth?)"

**Showcases:** Detects grouping-only query without entity/metric

---

### Scenario D: Year Without Context
**User:** "What about 2024?"

**Expected:**
- ❓ Asks: "What market data are you interested in for 2024?"
- ❓ Asks: "Which market or metric?"

**Showcases:** Detects year-only query without subject

---

## Part 3: Follow-Up Scenarios (Showcases Conversation Memory)

### Scenario E: Context-Aware Follow-Up

**Query 1:** "Show me electric vehicle market value in China for 2025"
- ✅ Returns China EV data for 2025

**Query 2 (Follow-up):** "How about USA?"
- ✅ System understands: "Show me electric vehicle market value in USA for 2025"
- ✅ Auto-resolves using conversation context
- Shows context badge: "Following up on: Electric Vehicles, 2025"

**Showcases:** Follow-up detection, query resolution, context awareness

---

### Scenario F: Dimension Modifier Follow-Up

**Query 1:** "Show me EV charging infrastructure market in 2025"
- ✅ Returns charging infrastructure data

**Query 2 (Follow-up):** "break it down by region"
- ✅ System understands: "Show me EV charging infrastructure by region in 2025"
- ✅ Adds GROUP BY region to previous query context

**Showcases:** Dimension addition in follow-ups

---

### Scenario G: Time Period Follow-Up

**Query 1:** "Show me electric vehicle markets in China"
- ✅ Returns China EV data (all available years)

**Query 2 (Follow-up):** "just 2024"
- ✅ System understands: "Show me electric vehicle markets in China in 2024"
- ✅ Adds time filter to previous query

**Showcases:** Temporal refinement in follow-ups

---

### Scenario H: Metric Change Follow-Up

**Query 1:** "Show me top EV markets by value in 2025"
- ✅ Returns top markets by market_value_usd_m

**Query 2 (Follow-up):** "now show volume instead"
- ✅ System understands: "Show me top EV markets by volume in 2025"
- ✅ Swaps metric from value to volume

**Showcases:** Metric switching in follow-ups

---

### Scenario I: Country Comparison Follow-Up

**Query 1:** "Electric vehicle market in China"
- ✅ Returns China EV data

**Query 2 (Follow-up):** "compare with USA"
- ✅ System understands: "Compare electric vehicle market in China vs USA"
- ✅ Adds comparison logic

**Showcases:** Comparison logic in follow-ups

---

### Scenario J: Multi-Turn Conversation

**Query 1:** "Show me electric vehicle markets in 2025"
- ✅ Returns global EV data

**Query 2 (Follow-up):** "only emerging markets"
- ✅ Adds is_emerging_market filter

**Query 3 (Follow-up):** "sort by growth forecast"
- ✅ Joins with forecast table, sorts by CAGR

**Showcases:** Multi-turn context preservation, progressive refinement

---

## Part 4: Advanced Scenarios (Showcase Reflection & Quality)

### Scenario K: Complex Aggregation

**User:** "Show me total EV ecosystem value by region - include batteries, charging, motors, and vehicles"

**Expected:**
- ✅ Joins 4 different markets
- ✅ Aggregates by region
- ✅ Reflection: "Query is complex but acceptable"
- ✅ Natural language explanation of insights

**Showcases:** Multi-market analysis, reflection agent, explanation generation

---

### Scenario L: Forecast Validation

**User:** "Compare 2024 actual results vs 2024 forecasts for electric vehicles"

**Expected:**
- ✅ Joins fact_market_size and fact_forecasts
- ✅ Shows forecast accuracy
- ✅ Calculates forecast error %

**Showcases:** Cross-fact table analysis, accuracy metrics

---

## Demo Flow Recommendations

### **Opening (3 mins) - Core Capabilities**
1. Query 1: "Show me the top 5 electric vehicle markets in 2025"
2. Query 2: "Compare electric vehicle market size between USA and China in 2025"
3. Query 8: "Compare base case vs optimistic forecast for 2026"

**Message:** "Basic analytics work out of the box"

---

### **Middle (5 mins) - AI Intelligence**

**Clarification:**
4. Query: "Show me the trends" → AI asks clarification
5. Clarify: "Electric vehicle market trends in 2025" → Returns data

**Follow-Ups:**
6. Query: "Show me EV charging infrastructure in China for 2025"
7. Follow-up: "How about USA?" → AI resolves context
8. Follow-up: "What about 2024?" → AI adds time filter

**Message:** "The AI understands context and asks smart questions"

---

### **Closing (2 mins) - Complex Analytics**
9. Query: "Which emerging markets have the highest EV growth forecast?"
10. Query: "Show me the EV ecosystem value - batteries, charging, motors, vehicles in 2025"

**Message:** "Handles complex multi-table analysis with natural language explanations"

---

## Quick Test Script

```bash
# Test all working queries
curl -X POST http://localhost:5001/query-agentic \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the top 5 electric vehicle markets in 2025", "client_id": 1}'

curl -X POST http://localhost:5001/query-agentic \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare USA and China electric vehicle markets in 2025", "client_id": 1}'

curl -X POST http://localhost:5001/query-agentic \
  -H "Content-Type: application/json" \
  -d '{"query": "Which emerging markets have highest EV growth forecast", "client_id": 1}'
```

---

## Guaranteed Working Queries (Based on Actual Data)

### ✅ Set 1: Market Overview
1. "Show me the top 5 electric vehicle markets in 2025"
2. "What's the total EV battery market value in 2025"
3. "List all available EV-related markets"
4. "Show me EV charging infrastructure market in 2025"

### ✅ Set 2: Geographic Analysis
5. "Compare USA and China electric vehicle markets in 2025"
6. "Show me electric vehicle market value in India"
7. "Which countries have the highest EV market value"
8. "Show me EV markets in Asia Pacific region"

### ✅ Set 3: Temporal Analysis
9. "Show electric vehicle market growth from 2024 to 2025"
10. "What's the quarterly trend for electric vehicles in 2025"
11. "Compare 2024 vs 2025 EV market value"
12. "Show me market trends for the last 2 years"

### ✅ Set 4: Emerging Markets
13. "Which emerging markets have the highest EV growth forecast"
14. "Show me electric vehicle market in India, Brazil, and Thailand"
15. "Compare emerging vs developed markets for EVs"

### ✅ Set 5: Forecasts & Scenarios
16. "Show me electric vehicle forecast for 2026"
17. "Compare base case vs optimistic forecast for 2026"
18. "What's the optimistic scenario for EV batteries in 2026"

### ✅ Set 6: Currency & Value Types
19. "Show me EV market value in constant USD"
20. "Compare current vs constant USD for electric vehicles"

---

## Clarification Demo Flows

### Flow 1: Ambiguous Query → Clarification → Success
```
User: "Show me the trends"
AI: ❓ "What market are you interested in? Which time period?"

User: "Electric vehicle trends in 2025"
AI: ✅ [Returns EV trend data for 2025]
```

### Flow 2: Fragment → Clarification → Success
```
User: "by region"
AI: ❓ "What data would you like to see? What metric?"

User: "EV market value by region in 2025"
AI: ✅ [Returns regional breakdown]
```

### Flow 3: Location Only → Clarification → Success
```
User: "China"
AI: ❓ "What would you like to know about China?"

User: "Electric vehicle market value in China"
AI: ✅ [Returns China EV data]
```

---

## Follow-Up Demo Flows

### Flow 4: Country Follow-Up
```
User: "Show me electric vehicle market in China for 2025"
AI: ✅ [Returns China data, saves context]

User: "How about USA?"
AI: ✅ [Auto-resolves to: "Show me electric vehicle market in USA for 2025"]
     Shows context badge: "Following up on: Electric Vehicles, 2025"
```

### Flow 5: Time Refinement Follow-Up
```
User: "Show me EV charging infrastructure market"
AI: ✅ [Returns charging data for all years]

User: "just 2025"
AI: ✅ [Filters to 2025 data only]
```

### Flow 6: Metric Switch Follow-Up
```
User: "Top 5 electric vehicle markets by value in 2025"
AI: ✅ [Returns ranked by market_value_usd_m]

User: "now show by volume instead"
AI: ✅ [Switches to market_volume_units]
```

### Flow 7: Dimension Addition Follow-Up
```
User: "Show me electric vehicle market value in 2025"
AI: ✅ [Returns aggregated EV value]

User: "break it down by region"
AI: ✅ [Adds GROUP BY region]
```

### Flow 8: Multi-Turn Conversation
```
User: "Show me electric vehicle markets"
AI: ✅ [Returns global EV data]

User: "only emerging markets"
AI: ✅ [Filters to India, Brazil, Thailand, etc.]

User: "sort by forecast growth"
AI: ✅ [Joins forecast table, sorts by CAGR]
```

---

## Part 5: Advanced Capabilities

### Query A: Complex Multi-Market Analysis
**User:** "Show me total EV ecosystem value by region - include batteries, charging infrastructure, motors, and vehicles in 2025"

**Expected:**
- ✅ Aggregates 4 different markets
- ✅ Groups by region (Asia Pacific, North America, Europe)
- ✅ Shows comprehensive ecosystem view
- ✅ Natural language explanation

**Showcases:** Multi-market joins, complex aggregation, AI explanation

---

### Query B: Segment Breakdown
**User:** "Break down electric vehicle market by segment type in 2025"

**Expected:**
- ✅ Returns segment distribution
- ✅ Shows Premium, Standard, etc.
- ✅ Percentage calculations

**Showcases:** Segment dimension usage

---

### Query C: Currency Comparison
**User:** "Compare EV market value in current USD vs constant USD for 2025"

**Expected:**
- ✅ Shows both currency types side by side
- ✅ Demonstrates inflation impact
- ✅ Percentage difference

**Showcases:** Currency dimension, inflation analysis

---

## Demo Talking Points

### 1. **Natural Language Understanding**
- "Notice how you can ask in plain English"
- "No need to know SQL or table structures"
- "System understands market research terminology"

### 2. **Intelligent Clarification**
- "When queries are ambiguous, the AI asks smart questions"
- "Doesn't make assumptions - seeks clarity"
- "Provides helpful examples"

### 3. **Conversation Memory**
- "You can ask follow-up questions naturally"
- "System remembers previous context"
- "No need to repeat full query each time"

### 4. **Multi-Client Support**
- "Each client sees only their data"
- "Automatic client isolation"
- "Enterprise-grade security"

### 5. **Rich Data Context**
- "Multiple markets: EVs, batteries, charging, etc."
- "Geographic coverage: 20+ countries"
- "Time-series: 3 years actual + forecasts"
- "Multiple currencies and inflation-adjusted views"

---

## Demo Checklist

**Before Demo:**
- [ ] Backend running on port 5001
- [ ] Frontend running on port 5173
- [ ] Active dataset set to "market_size"
- [ ] Test Query 1 to verify connectivity
- [ ] Clear browser cache for clean UI

**During Demo:**
- [ ] Start with client selector (show 3 clients)
- [ ] Run 2-3 core queries (1, 3, 4)
- [ ] Demonstrate clarification (Scenario A or B)
- [ ] Demonstrate follow-up (Flow 4 or 5)
- [ ] Show conversation panel (Cmd/Ctrl + H)
- [ ] Show reflection & quality checks
- [ ] Show natural language explanations

**Demo Duration:** 10-15 minutes

---

## Troubleshooting

### If Query Returns 0 Rows:
1. Check client_id (use 1, 2, or 6)
2. Verify year range (2023-2025 available)
3. Check market name (use exact: "Electric Vehicles" not "EV")

### If Clarification is Too Aggressive:
- Use specific years: "in 2025" instead of "recently"
- Include both entity and metric: "electric vehicle market value"
- Avoid fragments: "Show me..." not "just..."

### If Follow-Up Doesn't Work:
- Ensure previous query succeeded
- Use same session_id
- Keep queries similar in context

---

## API Reference for Demo

### Health Check:
```bash
curl http://localhost:5001/health
```

### List Clients:
```bash
curl http://localhost:5001/clients
```

### Check Active Dataset:
```bash
curl http://localhost:5001/dataset/active
```

### Switch Dataset (if needed):
```bash
curl -X POST http://localhost:5001/dataset/active \
  -d '{"dataset_id": "market_size"}'
```

---

## Success Metrics

✅ **All 10 core queries work** (>0 rows returned)  
✅ **Clarification scenarios trigger** (4/4)  
✅ **Follow-ups resolve correctly** (5/5)  
✅ **Response time <10s** per query  
✅ **Natural language explanations** generated  
✅ **Client isolation enforced** (security validation passes)  

---

**Demo Status:** READY FOR CLIENT PRESENTATION 🎯  
**Architect Approval:** Winston 🏗️  
**Last Updated:** November 27, 2025

