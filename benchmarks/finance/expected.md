# Finance Benchmark - Expected Outputs

## Task 1: Policy Interpretation

### Expected Answer Format
```yaml
question_1:
  question: "What is the aggregate limit for professional liability?"
  answer: "$2,000,000 per policy period"
  citations:
    - section: "Coverage A - Professional Liability"
      page: 12
      quote: "The aggregate limit of liability shall be $2,000,000"
  confidence: 0.95
  notes: "Clear and unambiguous statement in policy"

question_2:
  question: "Are cyber incidents covered under general liability?"
  answer: "No, cyber incidents are explicitly excluded"
  citations:
    - section: "Exclusions"
      page: 28
      quote: "This policy does not apply to any claim arising from..."
    - section: "Cyber Liability Endorsement"
      page: 45
      quote: "Cyber coverage available via separate endorsement"
  confidence: 0.90
  notes: "Exclusion is clear, but endorsement option exists"
```

### Evaluation Checklist
- [ ] All 10 questions answered
- [ ] Each answer cites specific sections
- [ ] Page numbers provided
- [ ] Direct quotes included where applicable
- [ ] Confidence levels are reasonable (not all 1.0)
- [ ] Ambiguities flagged appropriately

---

## Task 2: Guideline Comparison

### Expected Output Format
```yaml
changes:
  additions:
    - id: ADD-001
      section: "4.2 Cyber Risk Assessment"
      significance: major
      description: "New requirement for cyber security questionnaire"
      impact: "All new business submissions require additional documentation"

    - id: ADD-002
      section: "6.1 ESG Considerations"
      significance: minor
      description: "Added ESG scoring as optional factor"
      impact: "No immediate impact, guidance only"

  deletions:
    - id: DEL-001
      section: "3.5 Terrorism Exclusion Waiver"
      significance: major
      description: "Removed ability to waive terrorism exclusion"
      impact: "All policies must include terrorism exclusion"

  modifications:
    - id: MOD-001
      section: "2.1 Minimum Premium"
      previous: "$5,000"
      current: "$7,500"
      significance: major
      description: "50% increase in minimum premium"
      impact: "Small accounts may become uneconomical"

summary:
  total_changes: 18
  major_changes: 7
  minor_changes: 11
  overall_impact: |
    The 2024 guidelines represent a significant tightening of
    underwriting standards, particularly in cyber risk and
    minimum premium requirements.
```

### Evaluation Checklist
- [ ] Minimum 15 changes identified
- [ ] Changes correctly categorized (add/delete/modify)
- [ ] Significance ratings appropriate
- [ ] Impact assessments accurate
- [ ] Summary captures key themes
- [ ] No false positives (formatting changes, etc.)

---

## Task 3: Compliance Risk Identification

### Expected Output Format
```yaml
risks:
  - id: RISK-001
    endorsement: "CGL-2024-003"
    category: "regulatory_non_compliance"
    severity: high
    finding: "Missing state-mandated cancellation notice period"
    regulation: "State Insurance Code § 2071"
    requirement: "30-day notice required for cancellation"
    current_language: "Policy may be cancelled with 10 days notice"
    remediation: "Amend to 30-day notice minimum"

  - id: RISK-002
    endorsement: "CGL-2024-005"
    category: "conflicting_terms"
    severity: medium
    finding: "Definition of 'occurrence' conflicts with base policy"
    details: "Endorsement uses claims-made trigger, base uses occurrence"
    remediation: "Clarify which trigger applies to endorsed coverage"

priority_ranking:
  - RISK-001  # Regulatory - must fix immediately
  - RISK-003  # Missing disclosure - high priority
  - RISK-002  # Conflict - medium priority
  - RISK-004  # Ambiguity - lower priority
```

### Evaluation Checklist
- [ ] All compliance gaps identified
- [ ] Correct regulation citations
- [ ] Severity ratings justified
- [ ] Remediation is actionable
- [ ] Priority ranking logical
- [ ] No major gaps missed

---

## Task 4: Rate Filing Analysis

### Expected Output Format
```yaml
analysis:
  loss_ratio_verification:
    filed_ratio: 0.65
    calculated_ratio: 0.647
    variance: 0.003
    status: "VERIFIED"
    work: |
      Incurred Losses: $12,350,000
      Earned Premium: $19,090,000
      Ratio: 12,350,000 / 19,090,000 = 0.647

  trend_factor_review:
    filed_trend: 1.08
    methodology: "Exponential fit to 5-year data"
    issues:
      - "COVID year (2020) included without adjustment"
      - "Trend line shows poor R² (0.72)"
    recommendation: "Exclude 2020 or apply adjustment factor"

  credibility_assessment:
    filed_credibility: 0.85
    calculated_credibility: 0.78
    formula_used: "Bühlmann credibility"
    expected_claims: 1,200
    actual_claims: 987
    status: "QUESTIONED"
    notes: "Filed credibility appears overstated"

  unsupported_changes:
    - line: "Inland Marine"
      change: "+12%"
      support: "Loss ratio only 0.45, trend negative"
      assessment: "Not supported by experience"

summary:
  strengths:
    - "Comprehensive loss data provided"
    - "Clear methodology documentation"
  weaknesses:
    - "Trend factor calculation issues"
    - "Credibility weighting questionable"
    - "One rate change unsupported"
  recommendation: "Request revised trend analysis before approval"
```

### Evaluation Checklist
- [ ] Loss ratio calculation verified with work
- [ ] Trend methodology reviewed
- [ ] Credibility properly assessed
- [ ] Unsupported changes flagged
- [ ] Summary is balanced and accurate
- [ ] Recommendation is appropriate

---

## Scoring Guide

### Per Task Scoring (0-100)

| Score | Description |
|-------|-------------|
| 90-100 | Expert-level analysis, ready for regulatory review |
| 80-89 | Professional quality, minor gaps |
| 70-79 | Competent analysis, some issues |
| 60-69 | Basic understanding, notable gaps |
| 50-59 | Partial completion, significant issues |
| < 50 | Major deficiencies |

---

## Task 5: Financial Statement Analysis

### Expected Output Format
```yaml
financials:
  revenue:
    2022: 45200000
    2023: 52800000
    2024: 58100000
    yoy_growth:
      2023: "16.8%"
      2024: "10.0%"

  ebitda:
    2022: 12500000
    2023: 14800000
    2024: 15200000

  net_income:
    2022: 8200000
    2023: 9500000
    2024: 9100000

risk_factors:
  - rank: 1
    factor: "Customer concentration"
    severity: high
    detail: "Top 3 customers represent 62% of revenue"
  - rank: 2
    factor: "Regulatory changes"
    severity: high
    detail: "Pending legislation could increase compliance costs 15-20%"

industry_comparison:
  revenue_growth: { company: "10.0%", industry: "12.5%", assessment: "Below average" }
  ebitda_margin: { company: "26.2%", industry: "22.0%", assessment: "Above average" }

executive_summary: |
  Company shows solid profitability but decelerating revenue growth.
  Key risk is customer concentration. Recommend hold with price target...
```

### Evaluation Checklist
- [ ] Revenue, EBITDA, net income extracted for all 3 years
- [ ] Year-over-year growth rates calculated correctly
- [ ] Top 5 risk factors identified with severity
- [ ] Industry comparison with benchmarks
- [ ] Executive summary is actionable
- [ ] All figures cite source sections

### Citation Quality Scoring

| Level | Description |
|-------|-------------|
| Excellent | Exact section, page, and relevant quote |
| Good | Section and page, paraphrased content |
| Adequate | Section reference only |
| Poor | General reference without specifics |
| None | No citation provided |
