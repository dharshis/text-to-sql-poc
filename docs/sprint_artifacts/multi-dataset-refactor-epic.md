# Epic: Multi-Dataset Refactor - Dataset-Agnostic Text-to-SQL Accelerator

## Epic Goal
Transform the Euromonitor-specific text-to-SQL POC into a **dataset-agnostic accelerator** that can be quickly adapted for different company databases, enabling rapid demo setup (4-6 hours vs days).

## Business Value
- **Sales Enablement:** Rapidly create demos for new prospective clients
- **Scalability:** Onboard new company datasets without code changes
- **Maintainability:** Clear separation between system code and dataset-specific knowledge

## Scope
**Phase 1 (This Epic):** em_market dataset refactoring only
- Remove all hardcoded dataset-specific references from code
- Move domain knowledge to configuration and metadata files
- Maintain 100% of current functionality

**Phase 2 (Future):** Extend patterns to sales and market_size datasets

## Clarification: Multi-Dataset vs Multi-Client
- **Dataset** = Different company databases (Euromonitor, Acme Corp, Widget Industries)
- **Client/Corporation filtering** = Internal to each dataset (corp_id, client_id filtering)
- This epic focuses on **dataset portability**, NOT changing internal client isolation

## Success Metrics
- Zero hardcoded dataset-specific values in Python code
- New dataset onboarding: 4-6 hours (config + metadata files only)
- 100% behavior preservation for em_market dataset
- Clear onboarding documentation

## Stories
1. Story 1: Configuration Enhancement for Dataset-Agnostic Filtering
2. Story 2: Create Metadata Knowledge Pack for em_market Dataset
3. Story 3: Refactor ClaudeService for Hybrid Instruction Loading
4. Story 4: Refactor SQL Validator for Method-Driven Validation
5. Story 5: Frontend Configuration with Environment Variables
6. Story 6: Testing & Validation Suite
7. Story 7: Documentation & Onboarding Guide

## Timeline
- **Estimated Effort:** 2-3 days implementation + 1 day testing/docs
- **Total:** ~4 days for Phase 1 (em_market)

## Dependencies
- Existing metadata loader (already generic)
- Current config.json structure
- SQLite database for em_market

## Out of Scope
- Multi-tenant deployment architecture
- Non-SQLite database support
- Automated metadata generation
- Changes to internal client/corporation filtering logic
