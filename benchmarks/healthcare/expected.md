# Healthcare Benchmark - Expected Outputs

## Task 1: Coverage Eligibility Analysis

### Expected Output Format
```yaml
scenario_1:
  title: "Pre-existing condition after waiting period"
  member: "John Smith, DOB 1985-03-15"
  condition: "Type 2 Diabetes"
  enrollment_date: "2024-01-01"
  service_date: "2024-07-15"

  determination:
    status: "COVERED"
    rationale: |
      Member has completed the 6-month pre-existing condition
      waiting period. Diabetes management services are now
      covered under the policy terms.

  policy_references:
    - section: "Section 4.2 Pre-Existing Conditions"
      page: 23
      text: "Coverage for pre-existing conditions begins after 180 days"

  cost_sharing:
    deductible_applies: true
    deductible_remaining: 850.00
    copay: 30.00
    coinsurance: 0.20
    out_of_pocket_estimate: 180.00

  prior_authorization:
    required: false
    reason: "Routine diabetes management does not require PA"

  appeal_rights:
    applicable: false
    reason: "Claim is approved"

scenario_4:
  title: "Mental Health Parity"
  service: "Intensive Outpatient Program"

  determination:
    status: "COVERED"
    rationale: |
      Under MHPAEA, mental health benefits must be provided
      at parity with medical/surgical benefits. IOP coverage
      cannot be more restrictive than comparable medical
      intensive services.

  parity_analysis:
    medical_comparator: "Physical therapy intensive program"
    medical_visit_limit: "None"
    mh_visit_limit: "30 per year"
    parity_violation: true
    required_action: "Remove annual visit limit for IOP"
```

### Evaluation Checklist
- [ ] All 8 scenarios analyzed
- [ ] Determinations are correct
- [ ] Cost-sharing calculations accurate
- [ ] Prior auth requirements identified correctly
- [ ] Policy citations specific and accurate
- [ ] Parity issues identified where applicable
- [ ] Appeal rights explained when relevant

---

## Task 2: Policy Exclusion Identification

### Expected Output Format
```yaml
exclusion_inventory:
  absolute_exclusions:
    - id: EXC-001
      category: "Cosmetic"
      policy_section: "Section 8.1"
      page: 45
      language: "Cosmetic surgery or procedures primarily for appearance"
      exceptions:
        - "Reconstructive surgery following mastectomy"
        - "Repair of congenital defects in children under 18"
      state_mandate_conflict: false

    - id: EXC-002
      category: "Experimental"
      policy_section: "Section 8.3"
      page: 47
      language: "Experimental or investigational treatments"
      exceptions:
        - "Coverage required for qualified clinical trials (ACA)"
      state_mandate_conflict: true
      conflict_detail: "State requires coverage for Phase III trials"

  conditional_exclusions:
    - id: EXC-010
      category: "Infertility"
      policy_section: "Section 8.7"
      page: 52
      language: "Fertility treatments including IVF"
      condition: "Excluded unless fertility rider purchased"
      state_mandate_conflict: true
      conflict_detail: "State mandates basic infertility coverage"

  time_limited_exclusions:
    - id: EXC-020
      category: "Pre-existing"
      policy_section: "Section 4.2"
      page: 23
      language: "Conditions treated in prior 12 months"
      duration: "180 days from enrollment"
      exceptions:
        - "Pregnancy"
        - "Genetic conditions in newborns"

summary:
  total_exclusions: 28
  absolute: 15
  conditional: 8
  time_limited: 5
  state_mandate_conflicts: 3
  flagged_for_review: 2
```

### Evaluation Checklist
- [ ] All exclusions identified
- [ ] Correct categorization (absolute/conditional/time-limited)
- [ ] Exceptions to exclusions documented
- [ ] State mandate conflicts identified
- [ ] Problematic exclusions flagged
- [ ] Page/section references accurate

---

## Task 3: Claim Adjudication Rules

### Expected Output Format
```yaml
adjudication_rules:
  office_visits:
    codes: ["99211", "99212", "99213", "99214", "99215"]
    decision_tree:
      - step: 1
        check: "Is member eligible on date of service?"
        if_no: "DENY - Eligibility"
      - step: 2
        check: "Is provider in-network?"
        if_no: "Apply OON benefits"
      - step: 3
        check: "Is E/M level supported by documentation?"
        if_no: "Downcode to supported level"
      - step: 4
        check: "Are there other services same day?"
        if_yes: "Check bundling rules"

    medical_necessity:
      criteria:
        - "Documented chief complaint"
        - "Examination findings recorded"
        - "Assessment and plan present"
      documentation_required:
        - "Progress note or office note"
        - "Diagnosis codes"

    bundling_rules:
      - "99211-99215 bundle into surgical procedures same day"
      - "Separate E/M payable with modifier 25 if significant"

    payment:
      in_network: "Contracted rate"
      out_of_network: "150% of Medicare allowable"

  emergency_services:
    codes: ["99281", "99282", "99283", "99284", "99285"]
    decision_tree:
      - step: 1
        check: "Is this a true emergency (prudent layperson)?"
        if_yes: "Pay at in-network level regardless of provider"
        if_no: "Apply standard network rules"
      - step: 2
        check: "Was member admitted?"
        if_yes: "Apply inpatient benefits from admission"

    prudent_layperson_standard: |
      Emergency is defined as symptoms of sufficient severity
      that a prudent layperson with average health knowledge
      would reasonably expect absence of immediate care to:
      - Place health in serious jeopardy
      - Cause serious impairment to bodily functions
      - Cause serious dysfunction of any organ or body part

    no_prior_auth: true
    balance_billing_protection: true
```

### Evaluation Checklist
- [ ] Decision trees for all 10 procedure types
- [ ] Medical necessity criteria clearly defined
- [ ] Documentation requirements specified
- [ ] Bundling rules addressed
- [ ] Edge cases handled
- [ ] Regulatory requirements incorporated

---

## Task 4: Appeals Review

### Expected Output Format
```yaml
appeal_review:
  case_number: "APL-2024-001234"
  member: "Jane Doe"
  date_of_service: "2024-06-15"

  original_claim:
    procedure: "Lumbar fusion surgery (CPT 22612)"
    billed_amount: 85000.00

  denial_summary:
    reason_code: "MN-002"
    reason: "Medical necessity not established"
    details: |
      Original denial based on failure to document
      conservative treatment trial of at least 6 months.

  appeal_arguments:
    - argument: "Conservative treatment completed"
      evidence: "Physical therapy notes (12 sessions)"
      evaluation: "SUPPORTED - Notes confirm 4 months PT"

    - argument: "Functional decline documented"
      evidence: "Physician statement, imaging"
      evaluation: "SUPPORTED - MRI shows progression"

    - argument: "Surgery is standard of care"
      evidence: "Medical literature cited"
      evaluation: "SUPPORTED - Consistent with guidelines"

  medical_records_review:
    conservative_treatment:
      required: "6 months"
      documented: "4 months physical therapy, 2 months medications"
      assessment: "Meets requirement"

    imaging:
      findings: "Grade II spondylolisthesis with neural compression"
      progression: "Documented worsening from 2023 to 2024"

    functional_status:
      baseline: "Unable to work, ADL limitations"
      post_conservative: "No improvement, some worsening"

  policy_application:
    relevant_sections:
      - "Section 5.3 Spine Surgery"
      - "Medical Policy SP-2024-001"
    requirements_met:
      - "Conservative treatment trial: YES"
      - "Imaging confirms pathology: YES"
      - "Functional impairment documented: YES"
      - "Board-certified surgeon: YES"

  recommendation:
    decision: "OVERTURN - Approve claim"
    rationale: |
      Upon review of the complete medical record, member has
      satisfied all medical necessity criteria. Original denial
      was based on incomplete documentation review. The appeal
      provides clear evidence of conservative treatment trial,
      documented pathology, and functional impairment.
    payment_amount: 45000.00
    payment_basis: "Network contracted rate"
```

### Evaluation Checklist
- [ ] Denial reason accurately summarized
- [ ] All appeal arguments evaluated
- [ ] Medical records thoroughly reviewed
- [ ] Policy terms correctly applied
- [ ] Recommendation is well-reasoned
- [ ] Documentation supports conclusion
- [ ] Objective and unbiased analysis

---

## Scoring Guide

### Per Task Scoring (0-100)

| Score | Description |
|-------|-------------|
| 90-100 | Expert analysis suitable for regulatory audit |
| 80-89 | Professional quality, minor gaps |
| 70-79 | Competent work, some issues |
| 60-69 | Basic understanding, notable gaps |
| 50-59 | Partial completion, significant issues |
| < 50 | Major deficiencies |

---

## Task 5: Prior Authorization Workflow

### Expected Output Format
```yaml
prior_auth_workflows:
  mri_advanced_imaging:
    procedure: "MRI / Advanced Imaging"
    decision_tree:
      - step: 1
        check: "Is the ordering provider in-network?"
        if_no: "Inform member of OON implications, proceed with PA"
      - step: 2
        check: "Has conservative treatment been tried (4+ weeks)?"
        if_no: "Request documentation of medical necessity"
      - step: 3
        check: "Does clinical indication match approved criteria?"
        if_yes: "APPROVE — standard turnaround"
        if_no: "Refer to peer-to-peer review"
    documentation_required:
      - "Clinical notes supporting indication"
      - "Prior imaging results if available"
      - "Conservative treatment history"
    turnaround:
      standard: "3 business days"
      expedited: "24 hours"
      urgent: "Concurrent with service"
    appeal_route: "First-level appeal within 30 days → External review"
```

### Evaluation Checklist
- [ ] Decision trees for all 6 procedures
- [ ] Documentation requirements listed per procedure
- [ ] Standard and expedited turnaround times
- [ ] Urgent pathway defined
- [ ] Appeal routes documented
- [ ] Regulatory turnaround requirements met

### Healthcare-Specific Criteria

- Correct use of medical terminology
- Understanding of parity requirements
- Proper application of medical necessity
- Recognition of regulatory requirements
- Appropriate clinical sensitivity
