# Attendance & Shift Compliance — Design Document

## 1. Architecture Overview

The system is designed as a **modular FastAPI application** backed by PostgreSQL.

```text
       Simulated Sources
 ┌────────┬────────┬────────┬─────────┐
 │Punches │ Roster │ Leave  │ Overtime│
 └────────┴────────┴────────┴─────────┘
                 ↓
            FastAPI / REST
                 ↓
             Ingestion
                 ↓
            PostgreSQL
                 ↓
          Reconciliation
                 ↓
       ┌─────────┴─────────┐
       ↓                   ↓
 Payable Hours      Compliance Rules
                           ↓
                    Flags / Exceptions
                           ↓
                       Results
```

The main processing stages are:

1. **Ingestion** — validate and store the four sources.
2. **Reconciliation** — combine source data and calculate payable hours.
3. **Compliance** — apply configurable rules.
4. **Results** — return payable hours, flags, and exceptions.

A modular monolith is preferred over microservices because the project does not require distributed deployment and the simpler architecture is easier to test and operate.

---

## 2. Data Model

The main entities are:

```text
Worker
  │
  ├── Shift Roster
  ├── Punch
  ├── Approved Leave
  ├── Overtime Approval
  └── Payable Result
          └── Exception
```

PostgreSQL is used because these entities have clear relationships and reconciliation requires queries across multiple sources.

---

## 3. Reconciliation Design

For each **worker + work date**, the reconciliation engine evaluates:

```text
Roster
  +
Punches
  +
Leave
  +
Overtime
       ↓
Payable hours
       +
Flags / Exceptions
```

The engine:

* Removes duplicate punches using a configurable time threshold.
* Pairs valid IN/OUT punches.
* Handles overnight shifts using the rostered work date.
* Checks punches against approved leave.
* Compares actual work beyond the roster with overtime approval.
* Produces payable hours only where the working interval can be determined safely.

The reconciliation logic is kept separate from the API layer so it can be unit tested independently.

---

## 4. Key Constraint-Driven Decisions

### Missing punches

**Constraint:** Workers may forget to punch out; the system must not assume midnight or blindly apply the roster.

**Decision:** Treat an unresolved missing IN/OUT punch as an exception.

**Trade-off:** This may delay payment for an unresolved record, but prevents invented hours and directly reduces overpayment risk.

### Duplicate punches

**Constraint:** Duplicate punches seconds apart are common.

**Decision:** Deduplicate punches within a configurable interval.

**Trade-off:** A short configurable threshold handles terminal noise without permanently embedding a specific assumption into business logic.

### Overtime

**Constraint:** Overtime may be worked without approval and must not be silently paid or dropped.

**Decision:** Compare actual worked time with overtime approvals and surface unapproved overtime.

**Trade-off:** The system avoids treating unapproved work as automatically approved while preserving visibility for review.

### Overnight shifts

**Constraint:** Shifts can cross midnight and must be attributed to the correct day.

**Decision:** Use the rostered/work date when associating overnight punches rather than simply grouping by calendar date.

### Compliance rules

**Constraint:** Only two compliance rules exist and they must be configurable.

**Decision:**

```text
MAX_CONTINUOUS_SHIFT_HOURS = 10
MAX_CONSECUTIVE_WORKING_DAYS = 6
```

The reconciliation logic does not hardcode these values.

### Flags vs exceptions

**Constraint:** A flag is payable; an exception is not payable until resolved.

**Decision:** Represent these as separate result states.

Example:

```text
>10 hour shift
→ payable
→ compliance flag

Missing OUT punch
→ unresolved
→ exception
```

---

## 5. Ground Truth & Re-runnability

Correct shifts are generated before biometric errors are introduced. The resulting ground truth provides a reference for validating calculated hours.

The same pay period can also be processed repeatedly without creating duplicate results or exceptions. This supports correction and reprocessing of source data.

---

## 6. Scope

The design intentionally excludes:

* Real external system integrations
* Frontend or approval UI
* Payroll payment execution
* Labour-law research
* Automatic resolution of exceptions

These are outside the supplied project requirements.

## 7. Summary

The architecture prioritizes **correctness, traceability, and safe handling of uncertain attendance data** over unnecessary complexity.

The main design principle is:

> **Do not invent working hours when the available source data cannot safely establish them.**

This is the level I'd submit: **README ≈ 2 pages, Design Doc ≈ 3–4 pages** depending on formatting. It demonstrates that you understood the constraints without burying the evaluator in unnecessary documentation.
