# General Knowledge Benchmark - Expected Outputs

## Task 1: Multi-Step Research & Summary

### Expected Output Structure
```markdown
# AI Regulation Impact: EU vs US Startup Innovation (2023-2024)

## Executive Summary
[200-word summary covering key findings, major differences, and
primary conclusion about innovation impact]

## Regulatory Landscape

### European Union - AI Act
- Risk-based classification framework
- High-risk AI systems requirements
- Compliance timeline and obligations
- Penalties and enforcement

### United States - Fragmented Approach
- Sector-specific regulations
- State-level initiatives
- Executive Order on AI (Oct 2023)
- Self-regulatory frameworks

### Key Differences
| Aspect | EU | US |
|--------|-----|-----|
| Approach | Comprehensive | Sectoral |
| Timeline | 2024-2026 rollout | Ongoing |
| Penalties | Up to 7% revenue | Varies |
| Scope | All AI systems | Targeted |

## Impact on Startups

### Funding Trends
[Data on AI startup funding EU vs US, with citations]

### Compliance Costs
[Estimated costs for startups, case studies]

### Pivot Stories
[Examples of startups that changed direction due to regulation]

## Innovation Metrics

### Patents Filed
[Comparative data with citations]

### Funding Rounds
[Quarter-by-quarter comparison]

### Exits (Acquisitions/IPOs)
[Analysis of exit activity]

## Expert Opinions

### Pro-EU Regulation
[Cited viewpoints supporting comprehensive regulation]

### Pro-US Approach
[Cited viewpoints supporting light-touch regulation]

## Conclusions and Predictions
[Synthesis and forward-looking analysis]

## Bibliography
[Full citation list, minimum 12 sources]
```

### Evaluation Checklist
- [ ] All 12 sources cited
- [ ] Executive summary within word limit
- [ ] Balanced viewpoints presented
- [ ] Data accurately represented
- [ ] Citations properly formatted
- [ ] Coherent narrative throughout
- [ ] Actionable insights provided

---

## Task 2: Cross-File Synthesis

### Expected Output Format
```yaml
timeline:
  - date: "2022-Q1"
    events:
      - type: "earnings"
        detail: "Revenue $45M, guidance raised"
      - type: "product"
        detail: "New platform announced for Q3"

  - date: "2022-Q2"
    events:
      - type: "personnel"
        detail: "CTO departure announced"
      - type: "funding"
        detail: "Series C closed at $100M"

discrepancies:
  - id: DISC-001
    category: "revenue"
    internal_claim: "Q3 2022 revenue growth 25%"
    public_claim: "Q3 2022 revenue growth 35%"
    source_internal: "quarterly_report_q3_2022.pdf, page 4"
    source_public: "press_release_2022_10_15.md"
    significance: high

  - id: DISC-002
    category: "product"
    internal_claim: "Platform launch delayed to Q2 2023"
    public_claim: "Platform on track for Q4 2022 launch"
    source_internal: "quarterly_report_q3_2022.pdf, page 8"
    source_public: "press_release_2022_09_01.md"
    significance: high

metrics_tracking:
  revenue:
    2022_Q1: 45000000
    2022_Q2: 48000000
    2022_Q3: 52000000
    2022_Q4: 55000000
    2023_Q1: 58000000
    2023_Q2: 54000000  # decline
    2023_Q3: 56000000
    2023_Q4: 62000000
    trend: "growth with Q2 2023 dip"

  headcount:
    2022_Q1: 450
    2022_Q2: 520
    2022_Q3: 580
    2022_Q4: 620
    2023_Q1: 600  # layoffs
    2023_Q2: 580
    2023_Q3: 590
    2023_Q4: 610
    trend: "rapid growth then contraction"

sentiment_analysis:
  leadership_tone:
    2022: "aggressive growth, bold predictions"
    2023_H1: "cautious, focus on efficiency"
    2023_H2: "recovering confidence, measured optimism"

  analyst_sentiment:
    average_rating: 3.2  # out of 5
    trend: "declining through 2023"

concerns:
  - priority: high
    area: "Revenue reporting"
    detail: "Consistent gap between internal and external figures"

  - priority: medium
    area: "Product delays"
    detail: "Pattern of optimistic announcements, later delays"

  - priority: medium
    area: "Leadership stability"
    detail: "CTO and two VPs departed within 12 months"
```

### Evaluation Checklist
- [ ] Timeline complete and accurate
- [ ] All discrepancies identified
- [ ] Metrics correctly extracted
- [ ] Sentiment analysis reasonable
- [ ] Concerns prioritized appropriately
- [ ] Sources properly cited

---

## Task 3: Long-Running Workflow

### Expected Checkpoint Structure
```yaml
# After Phase 1: Data Collection
checkpoint_phase_1:
  workflow_id: "WF-2024-001"
  phase: "data_collection"
  status: "completed"
  timestamp: "2024-01-15T10:00:00Z"
  metrics:
    files_found: 10
    files_downloaded: 10
    total_size_bytes: 15728640
    duration_seconds: 45
  state:
    files:
      - name: "data_001.csv"
        status: "collected"
        size: 1048576
      - name: "data_002.json"
        status: "collected"
        size: 2097152
  next_phase: "validation"
  resumable: true

# After Phase 2: Validation
checkpoint_phase_2:
  workflow_id: "WF-2024-001"
  phase: "validation"
  status: "completed"
  timestamp: "2024-01-15T10:05:00Z"
  metrics:
    files_validated: 10
    passed: 8
    failed: 0
    warnings: 2
  issues:
    - file: "data_005.csv"
      type: "warning"
      message: "Missing values in 3 rows"
    - file: "data_008.json"
      type: "warning"
      message: "Deprecated field format"
  next_phase: "transformation"

# Final Audit Trail
audit_trail:
  workflow_id: "WF-2024-001"
  started: "2024-01-15T10:00:00Z"
  completed: "2024-01-15T10:20:00Z"
  phases:
    - phase: "data_collection"
      started: "2024-01-15T10:00:00Z"
      completed: "2024-01-15T10:00:45Z"
      status: "success"
    - phase: "validation"
      started: "2024-01-15T10:00:45Z"
      completed: "2024-01-15T10:05:00Z"
      status: "success"
    - phase: "transformation"
      started: "2024-01-15T10:05:00Z"
      completed: "2024-01-15T10:12:00Z"
      status: "success"
    - phase: "analysis"
      started: "2024-01-15T10:12:00Z"
      completed: "2024-01-15T10:18:00Z"
      status: "success"
    - phase: "report_generation"
      started: "2024-01-15T10:18:00Z"
      completed: "2024-01-15T10:20:00Z"
      status: "success"
  total_duration_seconds: 1200
  resume_events: 0
  errors_recovered: 0
```

### Evaluation Checklist
- [ ] All 5 phases completed
- [ ] Checkpoint created after each phase
- [ ] Checkpoints contain required information
- [ ] Resume functionality works
- [ ] Errors handled gracefully
- [ ] Audit trail complete and accurate

---

## Task 4: Reasoning Chain

### Expected Output Format
```markdown
# Scheduling Puzzle Solution

## Problem Understanding

### Entities
[List of 8 entities with their properties]

### Constraints
1. [Constraint 1 - parsed and restated]
2. [Constraint 2 - parsed and restated]
...
12. [Constraint 12 - parsed and restated]

### Optimization Objectives
1. [Objective 1 with priority]
2. [Objective 2 with priority]
3. [Objective 3 with priority]

## Constraint Analysis

### Dependency Graph
[Which constraints depend on others]

### Conflicts Detected
- Constraints 3 and 7 potentially conflict when...
- Resolution: Prioritize constraint 3 based on...

## Solution Building

### Step 1: Fixed Assignments
[Entities with only one valid option]
Reasoning: Entity A must be in slot 3 because...

### Step 2: Propagation
[Consequences of Step 1]
Reasoning: Since A is in slot 3, B cannot be in slots 2-4...

### Step 3: Branching Point
Choice: Entity C in slot 2 vs slot 5
Exploring slot 2 first because...

### Step 4: Backtrack (if needed)
Slot 2 choice for C leads to violation of constraint 8.
Backtracking to try slot 5...

### Step 5: Complete Assignment
[Remaining entities placed]

## Final Solution

| Entity | Assignment | Notes |
|--------|------------|-------|
| A | Slot 3 | Forced by constraint 1 |
| B | Slot 6 | Only valid after A placed |
| C | Slot 5 | After backtrack |
...

## Verification

### Constraint Check
- [x] Constraint 1: A in slot 3 ✓
- [x] Constraint 2: B after A ✓
...

### Optimization Score
- Objective 1: Score 8/10
- Objective 2: Score 9/10
- Objective 3: Score 7/10
- Total: 24/30 (80%)

### Optimality Argument
This solution is optimal because...
[Or: Near-optimal because perfect solution would require
violating constraint X, this is the best feasible solution]
```

### Evaluation Checklist
- [ ] All constraints correctly parsed
- [ ] Dependency analysis accurate
- [ ] Reasoning steps explicit
- [ ] Backtracking documented if used
- [ ] Solution satisfies all constraints
- [ ] Verification complete
- [ ] Optimality claim justified

---

## Scoring Guide

### Per Task Scoring (0-100)

| Score | Description |
|-------|-------------|
| 90-100 | Exceptional quality, thorough and insightful |
| 80-89 | High quality, complete with minor gaps |
| 70-79 | Good quality, some areas need improvement |
| 60-69 | Adequate, notable gaps or issues |
| 50-59 | Partial completion, significant problems |
| < 50 | Major deficiencies or incomplete |

---

## Task 5: Competitive Analysis Report

### Expected Output Format
```yaml
comparison_matrix:
  products: ["ProductA", "ProductB", "ProductC", "ProductD", "ProductE"]
  criteria:
    performance:
      weight: 0.30
      scores: [85, 78, 92, 70, 88]
      evidence:
        ProductA: "Benchmark shows 1200 req/s throughput"
        ProductC: "Best-in-class at 1800 req/s"
    cost_value:
      weight: 0.25
      scores: [75, 90, 60, 85, 70]
    ease_of_integration:
      weight: 0.20
      scores: [80, 85, 70, 75, 90]
    support:
      weight: 0.15
      scores: [90, 70, 85, 60, 80]
    scalability:
      weight: 0.10
      scores: [85, 75, 95, 65, 80]

overall_scores:
  ProductA: 82.0
  ProductB: 80.5
  ProductC: 78.5
  ProductD: 73.5
  ProductE: 82.0

recommendation:
  top_pick: "ProductA"
  runner_up: "ProductE"
  justification: |
    ProductA offers the best balance of performance, support, and
    scalability. While ProductC leads in raw performance, its higher
    cost and integration complexity make ProductA the better overall choice.
```

### Evaluation Checklist
- [ ] All 5 products analyzed
- [ ] Comparison matrix complete with all criteria
- [ ] Scores backed by evidence from specs
- [ ] Weighted calculation mathematically correct
- [ ] Recommendation justified
- [ ] Trade-offs discussed

### Resumability Scoring

| Criteria | Points |
|----------|--------|
| Resumes without errors | 25 |
| No repeated work | 25 |
| Context fully restored | 25 |
| Completes successfully | 25 |
