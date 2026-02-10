# General Knowledge Benchmark Tasks

## Overview

This benchmark evaluates agent capabilities in multi-step reasoning, research synthesis, cross-document analysis, and long-running workflows. These tasks test general intelligence and workflow management.

---

## Task 1: Multi-Step Research & Summary

### Description
Research a complex topic across multiple sources and produce a comprehensive summary with citations.

### Topic
"The impact of AI regulation on startup innovation in the EU vs US (2023-2024)"

### Input
- `data/sources.yaml` - List of 12 source documents/URLs to analyze
- `data/research_template.md` - Required output structure

### Requirements
1. Analyze all 12 sources
2. Identify key regulatory differences (EU AI Act vs US approach)
3. Find startup impact data and case studies
4. Compare innovation metrics between regions
5. Synthesize findings into coherent narrative
6. Provide proper citations for all claims

### Output Structure
- Executive Summary (200 words)
- Regulatory Landscape (EU vs US comparison)
- Impact on Startups (funding, compliance costs, pivot stories)
- Innovation Metrics (patents, funding rounds, exits)
- Expert Opinions (for/against each approach)
- Conclusions and Predictions
- Full Bibliography

### Success Criteria
- All sources analyzed
- Balanced presentation of viewpoints
- Proper citations throughout
- Coherent narrative structure
- Actionable insights

---

## Task 2: Cross-File Synthesis

### Description
Analyze a set of related documents and extract patterns, contradictions, and insights.

### Input
- `data/reports/` - 8 quarterly reports from a fictional company (2022-2023)
- `data/press_releases/` - 15 press releases from same period
- `data/analyst_notes/` - 5 analyst reports

### Requirements
1. Build timeline of major events
2. Identify discrepancies between internal reports and public statements
3. Track key metrics across quarters
4. Analyze sentiment trends in communications
5. Flag potential concerns for stakeholders

### Analysis Areas
- Revenue growth claims vs actual numbers
- Headcount changes and announcements
- Product launch timelines (announced vs delivered)
- Market positioning evolution
- Leadership tone changes

### Success Criteria
- Complete timeline constructed
- All discrepancies identified
- Metrics accurately tracked
- Sentiment analysis reasonable
- Concerns well-documented

---

## Task 3: Long-Running Workflow

### Description
Execute a complex, multi-phase workflow with checkpoints and state preservation.

### Workflow Phases
1. **Data Collection** (10 files to process)
2. **Validation** (check data quality, flag issues)
3. **Transformation** (normalize, enrich, deduplicate)
4. **Analysis** (compute statistics, identify patterns)
5. **Report Generation** (create final output)

### Input
- `data/workflow_input/` - Raw data files (CSV, JSON, XML)
- `data/workflow_config.yaml` - Workflow configuration
- `data/validation_rules.yaml` - Data quality rules

### Requirements
1. Execute each phase completely before moving to next
2. Create checkpoint after each phase
3. Handle errors gracefully (retry, skip, or fail)
4. Support resume from any checkpoint
5. Generate audit trail

### Checkpoint Format
```yaml
checkpoint:
  phase: "validation"
  status: "completed"
  timestamp: "2024-01-15T10:30:00Z"
  files_processed: 10
  errors: 0
  warnings: 2
  next_phase: "transformation"
```

### Success Criteria
- All phases complete
- Checkpoints created correctly
- Resume works from any phase
- Errors handled appropriately
- Audit trail complete

---

## Task 4: Reasoning Chain

### Description
Solve a multi-step logical reasoning problem with explicit chain-of-thought.

### Input
- `data/puzzle.md` - Complex logic puzzle with multiple constraints

### Puzzle Type
A scheduling optimization problem with 8 entities, 12 constraints, and 3 optimization objectives.

### Requirements
1. Parse and understand all constraints
2. Identify constraint conflicts
3. Build solution incrementally
4. Explain each reasoning step
5. Provide optimal solution with proof

### Reasoning Steps Required
- Constraint extraction
- Dependency mapping
- Conflict detection
- Partial solution building
- Backtracking if needed
- Optimization across objectives
- Verification of solution

### Success Criteria
- All constraints satisfied
- Solution is optimal (or near-optimal with justification)
- Reasoning chain is explicit and valid
- Backtracking documented if used
- Verification step included

---

## Evaluation Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Completeness | 30% | All required elements present |
| Accuracy | 30% | Correct information and reasoning |
| Coherence | 20% | Logical flow and organization |
| Depth | 20% | Insight beyond surface level |

## Time Limits

- Task 1: 45 minutes
- Task 2: 35 minutes
- Task 3: 40 minutes
- Task 4: 30 minutes

---

## Task 5: Competitive Analysis Report

### Description
Compare 5 products from specification sheets and produce a structured recommendation report.

### Input
- `data/product_specs/` - 5 product spec sheets (markdown)
- `data/evaluation_criteria.yaml` - Weighted evaluation criteria

### Requirements
1. Extract key features from each product spec
2. Build comparison matrix across all criteria
3. Score each product (0-100) per criterion
4. Calculate weighted overall scores
5. Produce recommendation with justification

### Evaluation Criteria
- Performance (30%)
- Cost / Value (25%)
- Ease of integration (20%)
- Support / Documentation (15%)
- Scalability (10%)

### Success Criteria
- All 5 products analyzed
- Comparison matrix complete
- Scores justified with evidence
- Weighted calculation correct
- Recommendation is defensible

## Time Limits

- Task 1: 45 minutes
- Task 2: 35 minutes
- Task 3: 40 minutes
- Task 4: 30 minutes
- Task 5: 30 minutes

## Resumability Testing

Tasks 1, 2, and 3 will be interrupted at random points to test:
- State preservation
- Context recovery
- Seamless continuation

The agent should not repeat completed work after resume.
