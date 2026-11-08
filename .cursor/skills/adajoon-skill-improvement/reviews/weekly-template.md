# Weekly Review: YYYY-MM-DD

**Week Ending**: [Date]
**Reviewer**: [Your name]

---

## Stats

- **Code written**: X files changed, Y additions, Z deletions
- **PRs merged**: N
- **PRs reviewed**: N
- **Bugs found**: M
- **Bugs fixed**: M

---

## Patterns Observed

### ✅ Excellent (>90% adherence)
- [Pattern name from skill]: X% compliance
- Example: Type hints used consistently (100%)

### ✅ Good (70-90% adherence)
- [Pattern name]: X% compliance
- Example: Async/await usage (85%)

### ⚠️ Needs Work (50-70% adherence)
- [Pattern name]: X% compliance
- Example: Test coverage on edge cases (60%)

### ❌ Problem (<50% adherence or recurring issues)
- [Issue description]: X instances
- Example: 3 instances of missing input validation

---

## Skill Violations

List each violation to track patterns:

- **adajoon-security**: 3x missing input validation
  - channels.py line 45
  - auth.py line 78
  - votes.py line 112
  
- **adajoon-conventions**: 2x obvious comments
  - utils.py line 23 ("Get the user")
  - api.py line 67 ("Return the data")

- **adajoon-database**: 1x missing transaction
  - user_service.py line 156

**Total violations**: N
**Violation rate**: N violations / Total PRs = X%

---

## Positive Observations

What went well this week:
- Example: Excellent error handling in PR #234
- Example: Great test coverage in PR #241
- Example: Clear commit messages following conventions

---

## Learning Opportunities

What could be improved:
- Example: Need better examples of input validation in skills
- Example: Team confused about when to use transactions
- Example: Inconsistent error message formatting

---

## Next Week Focus

Priority areas for improvement:

1. **Priority 1**: [Specific action]
   - Example: Add comprehensive input validation examples to adajoon-security
   
2. **Priority 2**: [Specific action]
   - Example: Review all endpoint handlers for missing validation
   
3. **Priority 3**: [Specific action]
   - Example: Create validation helper functions

---

## Skill Updates Made This Week

- **adajoon-security v2.1.0**: Added input validation patterns section
- **adajoon-conventions v1.4.1**: Added 10 comment anti-pattern examples
- **adajoon-database v1.3.2**: Clarified transaction usage guidelines

---

## Action Items

- [ ] Update [skill-name] with [specific change]
- [ ] Review codebase for [pattern]
- [ ] Create [helper/tool/script]
- [ ] Discuss [topic] with team
- [ ] Schedule [meeting/review]

---

## Notes

Any additional observations, team feedback, or context:

---

**Next Review**: [Date of next weekly review]
