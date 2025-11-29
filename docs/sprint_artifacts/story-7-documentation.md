# Story 7: Documentation & Onboarding Guide

**Epic:** Multi-Dataset Refactor
**Priority:** MEDIUM
**Estimated Effort:** 4 hours
**Status:** Ready for Development

---

## User Story

**As a** developer onboarding a new company dataset
**I want** clear documentation on the multi-dataset architecture and onboarding process
**So that** I can add new datasets quickly without assistance

---

## Background

With the refactoring complete, we need comprehensive documentation explaining:
1. The hybrid architecture (code vs config vs metadata)
2. How to add a new company dataset
3. Troubleshooting common issues
4. Architecture decisions and rationale

---

## Acceptance Criteria

### AC1: Create Onboarding Guide
- [ ] Create file: `docs/onboarding-new-dataset.md`
- [ ] Include sections:
  - Prerequisites
  - Step 1: Database Setup
  - Step 2: Configuration
  - Step 3: Metadata Knowledge Pack Creation
  - Step 4: Testing
  - Step 5: Deployment
  - Common Issues & Troubleshooting
  - Time Breakdown

**Required content:**
- Clear step-by-step instructions
- Code examples for each step
- Expected time for each phase
- Validation checkpoints
- Troubleshooting tips

**Target audience:** Developers with basic Python/SQL knowledge

**Goal:** Enable someone to onboard a new dataset in 4-6 hours using this guide

### AC2: Create Architecture Documentation
- [ ] Create file: `docs/multi-dataset-architecture.md`
- [ ] Include sections:
  - Architecture Overview
  - Hybrid Approach Rationale
  - Component Responsibilities
  - Configuration Design
  - Metadata System Design
  - Data Flow Diagrams
  - Design Decisions

**Key diagrams:**
1. Component architecture (ASCII art)
2. Configuration flow (how config is consumed)
3. Metadata loading sequence
4. SQL generation pipeline

**Example:**
```
┌─────────────────┐
│  config.json    │  ← System settings (method, filter_field)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ClaudeService   │  ← Generic SQL rules (BASE_LLM_INSTRUCTIONS)
└────────┬────────┘
         │
         ├─→ Load metadata/em_market/llm_instructions.md
         │   (dataset-specific examples)
         │
         └─→ Build hybrid prompt:
             1. Base instructions
             2. Database schema
             3. Dataset-specific examples
             4. Filter instruction
```

### AC3: Update Main README
- [ ] Update `README.md` with new section: "Multi-Dataset Architecture"
- [ ] Add subsection: "Adding a New Dataset"
- [ ] Link to detailed onboarding guide
- [ ] Add badges/indicators for dataset support

**Example section:**
```markdown
## Multi-Dataset Architecture

This codebase is designed as a **dataset-agnostic accelerator** for text-to-SQL demos. You can quickly adapt it for different company databases.

### Current Datasets
- ✅ **Euromonitor Market Data (em_market)**: Global consumer goods market research
- ✅ **Sales Demo (sales)**: Retail sales demonstration data
- ✅ **Market Size (market_size)**: Market size tracking data

### Adding a New Dataset

Onboarding a new company dataset takes **4-6 hours**:

1. Add database file to `data/your_dataset/`
2. Add 5-line config entry to `backend/config.json`
3. Create metadata knowledge pack (`metadata/your_dataset/`)
4. Test and validate

**No code changes required!**

See [Onboarding Guide](docs/onboarding-new-dataset.md) for detailed instructions.

### Architecture

- **Hybrid approach**: Generic SQL rules in code, dataset-specific knowledge in metadata
- **Config-driven**: Filtering methods and field names from `config.json`
- **Metadata-powered**: Examples and domain knowledge from markdown files

See [Architecture Documentation](docs/multi-dataset-architecture.md) for details.
```

### AC4: Create Troubleshooting Guide
- [ ] Create file: `docs/troubleshooting-multi-dataset.md`
- [ ] Include common issues and solutions:

**Issues to cover:**
1. "No llm_instructions.md found" warning
2. SQL validation fails unexpectedly
3. Client selection dropdown empty
4. Generated SQL doesn't include filter
5. Metadata not loading
6. Config syntax errors

**Format per issue:**
```markdown
## Issue: SQL validation fails for valid queries

**Symptom:** Valid SQL with corp_id filter fails validation

**Cause:** Config `method` field doesn't match validation logic

**Solution:**
1. Check config.json for dataset
2. Verify `method` is either "row-level" or "brand-hierarchy"
3. Verify `filter_field` matches SQL field name
4. Example: If SQL uses corp_id, config should have `"filter_field": "corp_id"`

**Validation:**
```bash
python tests/test_sql_validator_refactor.py
```
```

### AC5: Document Configuration Schema
- [ ] Create file: `docs/configuration-schema.md`
- [ ] Document all config.json fields with:
  - Field name
  - Type
  - Required/Optional
  - Default value
  - Valid values
  - Example
  - Purpose

**Example:**
```markdown
## client_isolation.method

**Type:** String
**Required:** Yes
**Valid Values:** `"row-level"` | `"brand-hierarchy"`
**Default:** `"row-level"`

**Purpose:** Determines how client/corporation filtering is applied in SQL queries.

**Values:**
- `"row-level"`: Standard WHERE clause filtering (e.g., WHERE client_id = 123)
- `"brand-hierarchy"`: Filtering through entity hierarchy (e.g., JOIN with corp_id filter)

**Example:**
```json
"client_isolation": {
  "method": "brand-hierarchy",
  "filter_field": "corp_id",
  "filter_table": "Dim_Brand"
}
```

**Used by:** ClaudeService, SQL Validator
```

### AC6: Document Metadata File Formats
- [ ] Create file: `docs/metadata-file-formats.md`
- [ ] Document expected structure for:
  - `dataset_info.md` (sections, format, examples)
  - `llm_instructions.md` (sections, format, examples)
  - `query_patterns.md` (existing, reference)
  - Table metadata files (existing, reference)

**Include:**
- Required sections
- Optional sections
- Formatting guidelines
- Example content
- Best practices

### AC7: Create Quick Start Guide
- [ ] Create file: `docs/quickstart-multi-dataset.md`
- [ ] Super condensed version for experienced developers
- [ ] Bullet-point format, no explanations
- [ ] Copy-pasteable commands

**Example:**
```markdown
# Quick Start: Adding a New Dataset

1. **Database**
   ```bash
   mkdir -p data/newco
   cp /path/to/newco.db data/newco/newco.db
   ```

2. **Config** (edit `backend/config.json`)
   ```json
   "newco": {
     "id": "newco", "name": "NewCo", "db_path": "data/newco/newco.db",
     "client_isolation": {"enabled": true, "method": "row-level", "filter_field": "tenant_id"}
   }
   ```

3. **Metadata**
   ```bash
   mkdir -p metadata/newco
   # Create dataset_info.md (30 min)
   # Create llm_instructions.md (2-3 hours)
   ```

4. **Test**
   ```bash
   python tests/test_multi_dataset_refactor.py
   python app.py
   ```

Done! Total: 4-6 hours.
```

---

## Technical Notes

### Documentation Files to Create
1. `docs/onboarding-new-dataset.md` (comprehensive guide, 8-10 pages)
2. `docs/multi-dataset-architecture.md` (technical architecture, 5-7 pages)
3. `docs/troubleshooting-multi-dataset.md` (issue solutions, 3-4 pages)
4. `docs/configuration-schema.md` (config reference, 3-4 pages)
5. `docs/metadata-file-formats.md` (metadata reference, 4-5 pages)
6. `docs/quickstart-multi-dataset.md` (quick reference, 1-2 pages)

### Documentation Standards
- Use GitHub-flavored Markdown
- Include code examples with syntax highlighting
- Use emoji indicators sparingly (✅ for success, ⚠ for warnings)
- Add table of contents for long documents
- Use consistent heading hierarchy
- Include "See also" sections with cross-references

### Tone and Style
- Clear, concise, actionable
- Assume reader has basic technical knowledge
- Explain "why" not just "how"
- Use real examples from em_market dataset
- Include screenshots where helpful (optional)

---

## Testing

### Documentation Review Checklist
- [ ] All code examples are syntactically correct
- [ ] All file paths are accurate
- [ ] All commands have been tested
- [ ] Instructions are in logical order
- [ ] No typos or grammatical errors
- [ ] Cross-references work (no broken links)
- [ ] Diagrams are clear and accurate
- [ ] Troubleshooting steps are actionable

### User Testing (Optional)
- [ ] Have someone unfamiliar with refactoring follow the onboarding guide
- [ ] Track time taken
- [ ] Document any confusion points
- [ ] Update guide based on feedback

### Completeness Check
- [ ] Can a developer add a new dataset using only the documentation?
- [ ] Are all configuration fields documented?
- [ ] Are all metadata files explained?
- [ ] Are common issues covered?
- [ ] Is the architecture clear?

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] 6 documentation files created
- [ ] README.md updated with multi-dataset section
- [ ] All code examples tested
- [ ] Documentation review checklist completed
- [ ] Cross-references verified
- [ ] Code committed: "Story 7: Comprehensive documentation and onboarding guide"

---

## Dependencies
- **Depends on:** All previous stories (1-6)
- **Final story** in the epic

---

## Notes
- **Quality over quantity** - better to have 6 great docs than 20 mediocre ones
- Focus on the **user's journey** - what do they need to know, when?
- Include **real examples** from em_market wherever possible
- Make it **copy-pasteable** - developers should be able to copy commands directly
- **Test everything** - verify all commands and code examples work
- This documentation will be the **template for future onboarding** - make it good!

---

## Success Metrics
- New developer can add dataset in 4-6 hours using docs
- Zero questions about "where do I put this?"
- Zero questions about "what does this config field do?"
- Troubleshooting guide covers 80%+ of common issues
- Architecture document explains design decisions clearly

---

## Reference
See plan document section "Phase 5: Documentation & Onboarding Guide"

---

## Template Outline for Onboarding Guide

```markdown
# Onboarding Guide: Adding a New Dataset

## Table of Contents
1. Introduction
2. Prerequisites
3. Architecture Overview (brief)
4. Step-by-Step Instructions
   - Step 1: Database Setup
   - Step 2: Configuration
   - Step 3: Metadata Creation
   - Step 4: Testing
5. Validation Checklist
6. Common Issues
7. Next Steps
8. Support

## Introduction
[Purpose, audience, expected time]

## Prerequisites
[Required knowledge, tools, access]

## Architecture Overview
[Brief explanation of hybrid approach]

## Step 1: Database Setup (1 hour)
[Detailed instructions with commands]

## Step 2: Configuration (15 minutes)
[Config.json structure, fields, examples]

## Step 3: Metadata Creation (3-4 hours)
[dataset_info.md and llm_instructions.md creation]

## Step 4: Testing (1 hour)
[Test commands, validation steps]

## Validation Checklist
[Checkbox list of things to verify]

## Common Issues
[5-10 common problems and solutions]

## Next Steps
[What to do after successful onboarding]

## Support
[Where to get help, who to contact]
```
