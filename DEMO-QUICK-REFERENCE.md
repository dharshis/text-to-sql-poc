# Demo Quick Reference Card

## 🎯 3 Drill-Down Examples

### Example 1: Regional Analysis Deep Dive
```
1. "Show me our market performance by region"
2. "Why is Africa performing so well?"          ← Drill-down (adds region filter)
3. "How did it look in 2024?"                   ← Drill-down (adds time filter)
4. "Break it down by product category"          ← Drill-down (adds grouping)
```
**Demonstrates:** Progressive refinement, context maintained across 4 queries

---

### Example 2: Brand Performance Dive
```
1. "Show me brand performance across all markets"
2. "Focus on Le Creuset"                        ← Drill-down (filter to brand)
3. "How did Q4 look?"                           ← Drill-down (add quarter filter)
```
**Demonstrates:** Brand-specific analysis with time dimension

---

### Example 3: Time Series Analysis
```
1. "Show sales trends over time"
2. "Focus on 2023"                              ← Drill-down (filter to year)
3. "Break it down by quarter"                   ← Drill-down (add grouping)
4. "What happened in Q4?"                       ← Drill-down (filter to quarter)
```
**Demonstrates:** Temporal drill-down, natural time references

---

## 🔄 2 Pivot Examples

### Pivot 1: Topic Change (Regional → Brand)
```
Context: Currently analyzing Africa 2024 performance

Query: "Show me brand performance across all markets"
                    ↑ Pivot indicator: "across all" (not "in Africa")
                    
Result: Fresh analysis, Africa context dropped
```
**Demonstrates:** System detects topic change, starts fresh

---

### Pivot 2: Metric Change (Sales → Market Size)
```
Context: Currently analyzing Le Creuset Q4 sales

Query: "Show me total market size trends over the last 3 years"
                    ↑ Pivot indicator: Different metric + explicit scope
                    
Result: New analysis, Le Creuset context dropped
```
**Demonstrates:** Different fact table, explicit new scope

---

## 💡 Key Phrases That Signal Intent

### Drill-Down Indicators (Maintain Context)
- "for [X]" → Add filter
- "by [dimension]" → Add grouping  
- "in [time]" → Add time filter
- "what about [X]?" → Replace one aspect, keep rest
- "how did it look..." → Add perspective to existing scope
- "break it down..." → Add granularity

### Pivot Indicators (New Context)
- "show me [new topic]" → Fresh start
- "across all [X]" → Explicit broad scope (drops previous filters)
- "instead" → Replacement
- "now show..." → Topic change
- "forget that, show..." → Explicit reset

---

## 🚨 What to Watch in Logs

### Good Signs ✅
```
INFO: Query expanded: 'by region' → 'Show market performance by region'
INFO: Query unchanged (complete query): 'Show total sales...'
INFO: Added history entry: 'by region' (expanded: True)
```

### Safety Net Triggers ⚠️
```
WARNING: ⚠️  CORP_ID AUTO-INJECTION TRIGGERED
WARNING: Claude forgot to include the mandatory corp_id filter!
WARNING: ACTION REQUIRED: Review system prompt...
```
**This is GOOD** - safety net working. Goal: reduce frequency to zero.

### Bad Signs ❌
```
ERROR: Security validation failed
ERROR: Query expansion failed
```
**This needs investigation**

---

## 🎬 Demo Flow (10 minutes)

| Min | Action | Demo Point |
|-----|--------|------------|
| 0-2 | Drill-Down Example 1 (4 queries) | "Natural conversation flow" |
| 2-3 | Show logs (optional) | "Query expansion in action" |
| 3-5 | Pivot Example 1 (2 queries) | "Intelligent topic switching" |
| 5-7 | Drill-Down Example 2 (3 queries) | "Different dimension, same intelligence" |
| 7-9 | Pivot Example 2 (1 query) | "Fresh analysis, automatic security" |
| 9-10 | Q&A / Technical deep dive | "Architecture benefits" |

---

## 📊 Talking Points

### For Business Stakeholders
- "Ask follow-up questions naturally, like talking to an analyst"
- "System remembers your context - no need to repeat yourself"
- "Secure by design - every query automatically filtered to your data"

### For Technical Stakeholders
- "Pure LLM approach - no hardcoded rules or dataset-specific parsing"
- "Safety nets for critical requirements (security filters)"
- "50% reduction in context tokens, 200+ lines of code removed"

---

## 🔧 Troubleshooting

### If expansion seems wrong:
"The system is being conservative. Let me be more explicit: [rephrase]"

### If context gets lost:
"Let me include more detail: [add context words]"

### If corp_id auto-injects:
"Perfect! See the warning? Safety net working. We'll tune prompts to reduce this."

---

## ✅ Demo Success Checklist

Before demo:
- [ ] Backend running
- [ ] Frontend open, new conversation
- [ ] Logs visible (optional but impressive)
- [ ] This reference card handy

During demo:
- [ ] Start with drill-down (show context maintenance)
- [ ] Pivot to show topic change detection
- [ ] Mention security filter always present
- [ ] Show logs if technical audience

After demo:
- [ ] Offer technical deep dive if interested
- [ ] Mention Phase 2 features (ambiguity resolution, etc.)
- [ ] Collect feedback on query expansion behavior

---

**Print this card and keep it nearby during demo!** 📋

