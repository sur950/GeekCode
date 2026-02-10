# Finance/Policy Benchmark Tasks

## Overview

This benchmark evaluates agent capabilities in interpreting financial policies, compliance guidelines, and regulatory documents. Tasks require careful reading, cross-referencing, and accurate extraction of information.

---

## Task 1: Policy Interpretation

### Description
Analyze a commercial insurance policy document and answer specific coverage questions.

### Input
- `data/commercial_policy.pdf` - 45-page commercial insurance policy
- `data/questions.yaml` - 10 specific coverage questions

### Requirements
1. Read and understand the full policy document
2. Answer each question with specific policy references
3. Cite exact section numbers and page references
4. Identify any ambiguities or conflicting clauses
5. Provide confidence level for each answer

### Questions Include
- What is the aggregate limit for professional liability?
- Are cyber incidents covered under general liability?
- What is the deductible for property damage claims?
- Are independent contractors covered as insureds?
- What are the notice requirements for claims?

### Success Criteria
- All 10 questions answered
- Correct section citations for each answer
- Ambiguities identified and explained
- Confidence levels are calibrated

---

## Task 2: Guideline Comparison

### Description
Compare two versions of underwriting guidelines and identify all changes.

### Input
- `data/guidelines_v1.pdf` - Previous version (2023)
- `data/guidelines_v2.pdf` - Current version (2024)

### Requirements
1. Identify all additions in v2
2. Identify all deletions from v1
3. Identify all modifications
4. Categorize changes by significance (major/minor)
5. Summarize impact on underwriting decisions

### Success Criteria
- All changes identified (minimum 15 expected)
- Correct categorization of change types
- Accurate significance assessment
- Clear impact summary

---

## Task 3: Compliance Risk Identification

### Description
Review a set of policy endorsements and identify potential compliance risks.

### Input
- `data/endorsements/` - 8 policy endorsement documents
- `data/regulations.md` - Applicable regulatory requirements

### Requirements
1. Review each endorsement against regulations
2. Identify non-compliant language
3. Identify missing required disclosures
4. Flag conflicting terms between endorsements
5. Recommend remediation for each issue

### Risk Categories
- Regulatory non-compliance
- Missing mandatory provisions
- Ambiguous coverage terms
- Conflicting exclusions
- Inadequate disclosure

### Success Criteria
- All compliance gaps identified
- Specific regulation citations
- Actionable remediation recommendations
- Priority ranking of issues

---

## Task 4: Rate Filing Analysis

### Description
Analyze a rate filing and verify actuarial justifications.

### Input
- `data/rate_filing.pdf` - Rate filing document
- `data/loss_data.csv` - Historical loss experience
- `data/actuarial_standards.md` - Applicable standards

### Requirements
1. Verify loss ratio calculations
2. Check trend factor methodology
3. Validate credibility weighting
4. Identify unsupported rate changes
5. Summarize filing strengths and weaknesses

### Success Criteria
- Calculations verified with work shown
- Methodology issues identified
- Credibility assessment accurate
- Clear summary of findings

---

## Task 5: Financial Statement Analysis

### Description
Parse a 10-K annual filing and extract key financial metrics, trends, and risk factors.

### Input
- `data/10k_filing.md` - Simplified 10-K annual report
- `data/metrics_template.yaml` - Required metrics to extract

### Requirements
1. Extract revenue, EBITDA, net income for 3 years
2. Calculate year-over-year growth rates
3. Identify top 5 risk factors with severity ratings
4. Compare reported vs industry benchmarks
5. Produce executive summary with investment thesis

### Success Criteria
- All metrics accurately extracted
- Growth calculations correct
- Risk factors properly ranked
- Industry comparison reasonable
- Summary is actionable

---

## Evaluation Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Accuracy | 40% | Correct interpretation of documents |
| Citations | 25% | Proper references to source material |
| Completeness | 20% | All aspects addressed |
| Clarity | 15% | Clear, professional communication |

## Time Limits

- Task 1: 25 minutes
- Task 2: 20 minutes
- Task 3: 25 minutes
- Task 4: 30 minutes
- Task 5: 30 minutes

## Special Instructions

- All answers must include source citations
- Confidence levels required for interpretive answers
- Flag any areas requiring human review
- Note any document quality issues affecting analysis
