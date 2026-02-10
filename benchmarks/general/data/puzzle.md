# Scheduling Optimization Puzzle

## Problem Description

You are scheduling a week-long tech conference with 8 sessions across 5 time slots. Each session has specific requirements that must be satisfied.

## Entities (Sessions)

| ID | Session | Speaker | Topic | Duration |
|----|---------|---------|-------|----------|
| A | Keynote | Dr. Smith | AI Future | 2 slots |
| B | Workshop 1 | Prof. Jones | ML Basics | 2 slots |
| C | Workshop 2 | Dr. Lee | Deep Learning | 1 slot |
| D | Panel | Multiple | Ethics in AI | 1 slot |
| E | Demo | Ms. Chen | Product Demo | 1 slot |
| F | Networking | N/A | N/A | 1 slot |
| G | Lightning Talks | Various | Mixed | 1 slot |
| H | Closing | Dr. Smith | Wrap-up | 1 slot |

## Time Slots

| Slot | Time | Day |
|------|------|-----|
| 1 | 9:00-11:00 | Monday |
| 2 | 11:00-13:00 | Monday |
| 3 | 14:00-16:00 | Monday |
| 4 | 9:00-11:00 | Tuesday |
| 5 | 11:00-13:00 | Tuesday |

## Constraints

### Hard Constraints (Must be satisfied)

1. **Keynote First**: Session A (Keynote) must be in slot 1.

2. **Closing Last**: Session H (Closing) must be in slot 5.

3. **Same Speaker**: Dr. Smith presents both A and H. There must be at least 2 slots between them.

4. **Workshop Before Panel**: Both workshops (B and C) must occur before the panel (D).

5. **No Overlap**: No two sessions can occupy the same slot (except multi-slot sessions occupy consecutive slots).

6. **Consecutive Slots**: Multi-slot sessions (A and B) must use consecutive slots.

7. **Networking After Lunch**: Session F (Networking) must be in slot 3 (after lunch).

8. **Demo Before Closing**: Session E (Demo) must occur before session H.

### Soft Constraints (Optimization objectives)

9. **Workshop Spacing**: Ideally, workshops B and C should not be in consecutive slots (allows attendees to rest).

10. **Lightning Talks Energy**: Session G (Lightning Talks) performs best in morning slots (1, 2, or 4).

11. **Panel Engagement**: Session D (Panel) is better in afternoon (slot 3) or late morning (slot 2, 5).

12. **Demo Visibility**: Session E (Demo) gets better attendance in slot 4 or 5.

## Optimization Objectives (Ranked by priority)

1. **Maximize Constraint Satisfaction**: All hard constraints must be satisfied.

2. **Maximize Soft Constraint Score**: Each satisfied soft constraint adds 1 point.

3. **Minimize Speaker Fatigue**: Prefer more spacing between Dr. Smith's sessions.

## Your Task

1. Parse and understand all constraints
2. Identify any inherent conflicts
3. Build a valid schedule that satisfies all hard constraints
4. Optimize for soft constraints where possible
5. Explain your reasoning at each step
6. Verify your final solution against all constraints

## Expected Output Format

```yaml
solution:
  slot_1:
    session: [Session ID]
    justification: [Why this session here]
  slot_2:
    session: [Session ID]
    justification: [Why this session here]
  # ... continue for all slots

constraint_verification:
  hard_constraints:
    - id: 1
      description: "Keynote First"
      status: SATISFIED
      evidence: "A is in slot 1"
    # ... all constraints

  soft_constraints:
    - id: 9
      description: "Workshop Spacing"
      status: SATISFIED/VIOLATED
      score: 1/0
    # ... all soft constraints

optimization_score:
  hard_constraints: [X/8]
  soft_constraints: [Y/4]
  total: [Score]

reasoning_chain:
  - step: 1
    action: "Place A in slot 1"
    reason: "Constraint 1 requires Keynote first"
    remaining_options: [Updated option counts]
  # ... all reasoning steps
```

## Hints

- Start with the most constrained entities (A and H have fixed positions)
- Consider the implications of multi-slot sessions
- Work through constraints in order of restrictiveness
- Document any backtracking required
