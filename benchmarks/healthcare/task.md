# Healthcare/Medical Policy Benchmark Tasks

## Overview

This benchmark evaluates agent capabilities in healthcare policy interpretation, coverage eligibility analysis, and claims adjudication. Tasks require understanding of medical terminology, insurance concepts, and regulatory requirements.

---

## Task 1: Coverage Eligibility Analysis

### Description
Analyze a health insurance policy to determine coverage eligibility for specific medical scenarios.

### Input
- `data/health_policy.pdf` - Health insurance policy document
- `data/member_info.yaml` - Member demographics and plan details
- `data/scenarios.yaml` - 8 coverage scenarios to evaluate

### Scenarios Include
1. Pre-existing condition coverage after waiting period
2. Out-of-network emergency care
3. Experimental treatment request
4. Mental health parity compliance
5. Preventive care coverage
6. Durable medical equipment
7. Telehealth services
8. Prescription drug tier exception

### Requirements
1. Determine coverage status for each scenario
2. Identify applicable policy sections
3. Calculate member cost-sharing (deductible, copay, coinsurance)
4. Note any prior authorization requirements
5. Identify appeal rights if denied

### Success Criteria
- All 8 scenarios analyzed correctly
- Cost-sharing calculations accurate
- Prior auth requirements identified
- Policy citations provided
- Appeal rights explained

---

## Task 2: Policy Exclusion Identification

### Description
Review a health policy and create a comprehensive exclusion inventory.

### Input
- `data/comprehensive_policy.pdf` - Full health insurance policy
- `data/exclusion_template.yaml` - Standard exclusion categories

### Requirements
1. Identify all exclusions in the policy
2. Categorize by type (absolute, conditional, time-limited)
3. Note any exceptions to exclusions
4. Cross-reference with state mandates
5. Flag potentially problematic exclusions

### Exclusion Categories
- Pre-existing conditions
- Experimental/investigational
- Cosmetic procedures
- Custodial care
- Workers' compensation
- Motor vehicle (no-fault)
- War/terrorism
- Self-inflicted injury
- Fertility treatments
- Weight loss programs

### Success Criteria
- All exclusions identified
- Correct categorization
- Exceptions documented
- State mandate conflicts flagged
- Clear organization

---

## Task 3: Claim Adjudication Rules

### Description
Develop adjudication rules based on policy language and medical guidelines.

### Input
- `data/policy_benefits.pdf` - Benefit schedule and policy terms
- `data/medical_guidelines.md` - Clinical guidelines for common procedures
- `data/code_mappings.csv` - CPT/ICD-10 code mappings

### Requirements
1. Create decision logic for 10 common procedure types
2. Define medical necessity criteria
3. Specify documentation requirements
4. Establish payment hierarchy rules
5. Handle bundling/unbundling scenarios

### Procedure Types
1. Office visits (99211-99215)
2. Preventive exams
3. Diagnostic imaging
4. Laboratory services
5. Surgical procedures
6. Physical therapy
7. Mental health services
8. Emergency services
9. Ambulance transport
10. Durable medical equipment

### Success Criteria
- Clear decision trees for each procedure type
- Medical necessity criteria defined
- Documentation requirements specified
- Bundling rules addressed
- Edge cases handled

---

## Task 4: Appeals Review

### Description
Review a claims appeal package and prepare a determination recommendation.

### Input
- `data/appeal_package/`
  - `original_claim.yaml` - Original claim details
  - `denial_letter.pdf` - Initial denial letter
  - `appeal_letter.pdf` - Member's appeal letter
  - `medical_records.pdf` - Supporting medical documentation
  - `physician_statement.pdf` - Treating physician's statement

### Requirements
1. Summarize the original denial reason
2. Evaluate the appeal arguments
3. Review medical necessity documentation
4. Apply policy terms to the case
5. Provide recommendation with rationale

### Determination Options
- Overturn denial (approve claim)
- Uphold denial
- Partial approval
- Request additional information

### Success Criteria
- Accurate summary of case
- Fair evaluation of evidence
- Correct policy application
- Well-reasoned recommendation
- Clear documentation

---

## Evaluation Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Accuracy | 40% | Correct interpretation of policy and medical terms |
| Completeness | 25% | All relevant factors considered |
| Citations | 20% | Proper references to policy sections |
| Clarity | 15% | Clear, understandable explanations |

## Time Limits

- Task 1: 30 minutes
- Task 2: 25 minutes
- Task 3: 35 minutes
- Task 4: 30 minutes

---

## Task 5: Prior Authorization Workflow

### Description
Build a prior authorization decision tree from policy language for 6 common procedures.

### Input
- `data/prior_auth_policy.md` - Prior authorization requirements
- `data/procedure_list.yaml` - 6 procedures requiring PA

### Requirements
1. Create decision flowchart for each procedure
2. Define required documentation at each step
3. Specify turnaround time requirements
4. Include expedited/urgent pathways
5. Map appeal routes for denials

### Procedures
1. MRI/Advanced imaging
2. Specialty medications (biologics)
3. Inpatient surgery (non-emergency)
4. Outpatient behavioral health
5. Durable medical equipment (powered)
6. Home health services

### Success Criteria
- Complete decision trees for all 6 procedures
- Documentation requirements are specific
- Turnaround times match regulatory requirements
- Urgent pathways clearly defined
- Appeal routes documented

## Time Limits

- Task 1: 30 minutes
- Task 2: 25 minutes
- Task 3: 35 minutes
- Task 4: 30 minutes
- Task 5: 30 minutes

## Special Instructions

- Use standard medical terminology
- Apply HIPAA-compliant language
- Consider both policy terms AND medical guidelines
- Flag items requiring clinical review
- Maintain objectivity in appeal reviews
