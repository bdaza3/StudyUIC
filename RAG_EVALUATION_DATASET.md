# StudyUIC RAG Evaluation Dataset

This file defines representative test questions and expected retrieval outcomes for the RAG system.

Format:

```
## Category: [Retrieval Category]

### Question: [Question text]

**Expected Results:**
- [Expected document ID or course code]
- [Key content to find]

**Metadata Filters:**
- department: [if applicable]
- course_level: [if applicable]

**Metrics:**
- Recall@5: Expected to retrieve expected result
- MRR: Rank of first relevant result
```

---

## Category: Factual Lookup (Exact Prerequisite)

### Question 1: "What is the prerequisite for CS 251?"

**Expected Results:**
- CS 251 document
- Should contain "Prerequisites: CS 150 or equivalent"

**Metadata Filters:** None

**Evaluation:**
- Recall@1: CS 251 should be #1 result
- MRR: 1.0

---

### Question 2: "What are the prerequisites for CS 401?"

**Expected Results:**
- CS 401 document
- Should contain prerequisites field

**Metadata Filters:** None

**Evaluation:**
- Recall@1: CS 401 should rank high
- MRR: Expected high

---

## Category: Course Level Filtering

### Question 3: "What 400-level CS courses are available?"

**Expected Results:**
- CS 401, CS 412, CS 461 (or other 400-level courses)

**Metadata Filters:**
- department: CS
- course_level: 400

**Evaluation:**
- Recall@5: All 400-level CS courses should be retrievable
- Precision@5: Should only return 400-level courses

---

### Question 4: "What introductory CS courses should I take?"

**Expected Results:**
- CS 150, CS 151, or other 100-200 level CS courses

**Metadata Filters:**
- department: CS
- course_level: <= 200

**Evaluation:**
- Recall@5: Should retrieve introductory courses
- MRR: First introductory course should rank high

---

## Category: Semantic Course Relationships

### Question 5: "What courses can I take after CS 251?"

**Expected Results:**
- Courses with "Prerequisite: CS 251" or "Prerequisite: CS 251 or equivalent"
- Examples: CS 301, CS 361, CS 401, CS 412

**Metadata Filters:**
- department: CS

**Evaluation:**
- Recall@5: Should retrieve multiple courses with CS 251 as prerequisite
- MRR: First course requiring CS 251 as prerequisite

---

### Question 6: "What are the prerequisites for taking CS 461?"

**Expected Results:**
- CS 461 document with prerequisite information
- May reference CS 251, CS 401, or other courses

**Metadata Filters:** None

**Evaluation:**
- Recall@1: CS 461 should be top result
- MRR: 1.0

---

## Category: Multi-Document Retrieval

### Question 7: "What courses should I take if I'm interested in artificial intelligence?"

**Expected Results:**
- Multiple courses with AI-related keywords:
  - CS 401 (Algorithms)
  - CS 412 (AI/ML elective if available)
  - CS 461 (Advanced topics)
  - Possibly MATH courses (linear algebra, discrete math)

**Metadata Filters:** None

**Evaluation:**
- Recall@5: Should retrieve multiple AI-related courses
- MRR: First AI-related course should rank reasonably high

---

### Question 8: "What 300-level courses should I take before advanced CS electives?"

**Expected Results:**
- CS 301, CS 361 (or other 300-level prerequisites)
- Courses that serve as prerequisites for 400-level courses

**Metadata Filters:**
- department: CS
- course_level: 300

**Evaluation:**
- Recall@5: Should retrieve relevant 300-level courses
- Precision@5: Should not include non-prerequisite courses

---

## Category: Department-Specific Queries

### Question 9: "What math courses are available for computer science majors?"

**Expected Results:**
- MATH 310 (Linear Algebra)
- MATH 210, MATH 220 (if available)
- Any MATH courses relevant to CS

**Metadata Filters:**
- department: MATH

**Evaluation:**
- Recall@5: Should retrieve relevant math courses
- MRR: First relevant math course

---

### Question 10: "What engineering courses are related to embedded systems?"

**Expected Results:**
- ECE 266 (Embedded Systems Design)
- Related ECE courses

**Metadata Filters:**
- department: ECE

**Evaluation:**
- Recall@5: Should retrieve embedded systems course
- MRR: ECE 266 should rank high

---

## Category: No-Answer / Out-of-Scope Questions

### Question 11: "What is the average salary for a CS graduate from UIC?"

**Expected Results:**
- NONE (data not in academic database)

**Metadata Filters:** None

**Evaluation:**
- Correct behavior: Return empty result or "no relevant documents"
- Should NOT invent answer

---

### Question 12: "What is the mascot of UIC?"

**Expected Results:**
- NONE (not academic course data)

**Metadata Filters:** None

**Evaluation:**
- Correct behavior: Return empty result
- Should NOT hallucinate

---

## Category: Ambiguous / Clarification Queries

### Question 13: "Can I take CS 251 next semester?"

**Expected Results:**
- CS 251 document (for reference)
- BUT: Cannot determine "can I" without knowing prerequisites/current courses

**Metadata Filters:** None

**Evaluation:**
- Retrieves CS 251: ✓
- But cannot answer feasibility without more context
- MRR: CS 251 should rank high

---

### Question 14: "What's the easiest CS class?"

**Expected Results:**
- AMBIGUOUS: "Easiest" is subjective
- Could return multiple CS courses

**Metadata Filters:** None

**Evaluation:**
- Should retrieve CS courses
- Acknowledge ambiguity (future LLM stage)

---

## Category: Malformed / Edge Case Queries

### Question 15: "CSsss"

**Expected Results:**
- NONE or minimal partial match

**Metadata Filters:** None

**Evaluation:**
- Should handle gracefully
- Should NOT crash

---

### Question 16: "     "

**Expected Results:**
- Error: Empty/whitespace query

**Metadata Filters:** None

**Evaluation:**
- Should validate and reject
- Should NOT return random results

---

## Category: Credit/Requirements Lookups

### Question 17: "How many credits is CS 251?"

**Expected Results:**
- CS 251 document with credits field
- Should contain "Credits: 3" (or actual credit value)

**Metadata Filters:** None

**Evaluation:**
- Recall@1: CS 251 should be top result
- MRR: 1.0

---

### Question 18: "What 3-credit CS courses are available?"

**Expected Results:**
- Multiple courses with 3 credits

**Metadata Filters:**
- department: CS

**Evaluation:**
- Recall@5: Should retrieve multiple 3-credit courses
- Precision@5: Should only return 3-credit courses

---

## Category: Cross-Department Prerequisites

### Question 19: "What CS courses require MATH 310?"

**Expected Results:**
- Courses with "Prerequisites: MATH 310" or similar

**Metadata Filters:**
- department: CS (optional)

**Evaluation:**
- Recall@5: Should find courses requiring MATH 310
- MRR: First course with MATH 310 prerequisite

---

### Question 20: "What courses are prerequisites for CS 401?"

**Expected Results:**
- CS 251 (and possibly others)

**Metadata Filters:**
- department: CS

**Evaluation:**
- Recall@3: Should find CS 251 and other prerequisites
- MRR: First prerequisite course

---

## Baseline Metrics

### Expected Performance

For Phase 2 (complete retrieval system):

- **Factual Lookup (Q1-2, 17):** Recall@1 ≥ 95%, MRR ≥ 0.95
- **Level Filtering (Q3-4):** Precision@5 ≥ 90%
- **Semantic Search (Q5-8):** Recall@5 ≥ 80%, MRR ≥ 0.70
- **Department Queries (Q9-10):** Recall@5 ≥ 85%
- **No-Answer (Q11-12):** 100% correct rejection
- **Edge Cases (Q15-16):** 100% graceful handling

### Regression Testing

When retrieval logic changes, rerun against this dataset:

```bash
pytest tests/test_rag_evaluation.py --metric recall@5 --baseline baseline.json
```

Should not degrade metrics by >5% without explicit approval.

---

## Future Additions

- Add IDS (Interdisciplinary Studies) courses
- Add more domain-specific prerequisite chains
- Add edge cases for prerequisites from other schools
- Add questions about course schedules (future capability)
- Add program/degree requirement questions (future capability)

