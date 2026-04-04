---
name: adajoon-skill-improvement
description: Implements continuous improvement process for Cursor skills following Karpathy-style learning methodologies. Use when reviewing code, after bugs/incidents, during retrospectives, or when the user mentions "improve skills", "update guidelines", "skill feedback", or needs to document patterns, track deviations, or evolve coding standards.
---

# Adajoon Skill Improvement

Systematic approach to evolving Cursor skills through iterative refinement and meta-learning.

## Core Philosophy

**Learn by doing**: Skills improve through real implementation feedback, not speculation.

**Track everything**: Patterns that work, deviations that occur, corrections needed.

**Iterate fast**: Small, frequent updates beat large, delayed rewrites.

**Measure impact**: Know which skills prevent bugs, which need clarification.

---

## When to Trigger

Apply this skill during:

1. **Code Review** - Note patterns violated or followed
2. **Bug Postmortems** - Update skills to prevent recurrence
3. **Repetitive Corrections** - If fixing the same issue 3+ times
4. **Performance Issues** - Document optimization patterns
5. **Security Incidents** - Update security skill immediately
6. **Weekly Reviews** - Aggregate learnings
7. **Monthly Audits** - Measure skill effectiveness

---

## Iterative Refinement Process

### 1. Capture Deviations

When reviewing code or fixing bugs, document deviations from skills:

```markdown
## Deviation Log

**Date**: 2026-04-04
**Skill**: adajoon-security
**Deviation**: API key stored in code instead of environment variable
**Location**: `backend/app/services/external_api.py:15`
**Impact**: Critical - exposed in git history
**Root Cause**: Skill didn't emphasize scanning for hardcoded secrets
**Fix**: Added pre-commit hook + updated skill section on secrets detection
```

**Template location**: `.cursor/skills/adajoon-skill-improvement/logs/deviations.md`

### 2. Track Pattern Effectiveness

Document which patterns work vs fail in practice:

```markdown
## Pattern Effectiveness Log

**Pattern**: "Use async/await for all database operations"
**Skill**: adajoon-conventions
**Status**: ✅ WORKING
**Evidence**: Zero sync DB calls in last 50 PRs
**Notes**: Clear examples in skill make this obvious

---

**Pattern**: "Only comment non-obvious intent"
**Skill**: adajoon-conventions
**Status**: ⚠️ NEEDS CLARITY
**Evidence**: 3 PRs this week had obvious comments flagged
**Notes**: Add more examples of what counts as "obvious"
```

**Template location**: `.cursor/skills/adajoon-skill-improvement/logs/patterns.md`

### 3. Code Review Feedback Loop

During code reviews, systematically check:

**Checklist**:
- [ ] Which skills were violated?
- [ ] Was the violation skill content missing or unclear?
- [ ] Could better examples prevent this?
- [ ] Is this a new pattern to document?
- [ ] Should we add a validation script?

**Quick log**:
```bash
# In PR comments, tag skill issues with:
[SKILL:adajoon-conventions] Use f-strings instead of .format()
[SKILL:adajoon-security] Missing input validation on user_id parameter
[SKILL:NEW] Consider documenting this React context pattern
```

---

## Learning by Doing

### Document Mistakes and Fixes

After fixing any bug, create a learning entry:

```markdown
## Learning Entry #042

**Date**: 2026-04-04
**Category**: Database
**Mistake**: Missing database transaction caused partial updates
**What Happened**: User profile updated but related preferences failed
**Why It Happened**: Transaction not wrapped properly in async context
**The Fix**:
\`\`\`python
async with db.begin():
    await db.execute(update_user)
    await db.execute(update_preferences)
\`\`\`
**Skill Update**: Added transaction patterns to adajoon-database skill
**Prevention**: Added example of multi-table updates requiring transactions
```

**Template location**: `.cursor/skills/adajoon-skill-improvement/learnings/YYYY-MM-DD-issue-number.md`

### Test Assumptions

Before adding new patterns to skills, validate them:

```markdown
## Assumption Test

**Hypothesis**: Using SELECT FOR UPDATE improves concurrent vote handling
**Test Plan**: 
1. Add FOR UPDATE to vote queries
2. Run concurrent vote test (100 simultaneous votes)
3. Measure deadlocks, race conditions, performance

**Results**:
- Deadlocks: 0 (was 12 without FOR UPDATE)
- Race conditions: 0 (was 5 without)
- Performance: +15ms per query (acceptable trade-off)

**Conclusion**: ✅ Add to adajoon-database skill
**Added**: Section "Concurrent Updates" with SELECT FOR UPDATE pattern
```

---

## Self-Review Process

### Before Committing Code

Run through skill checklist:

```bash
# Create pre-commit mental checklist
echo "Running skill self-review..."

# For Python changes:
- [ ] Type hints on all functions? (adajoon-conventions)
- [ ] Using async/await? (adajoon-conventions)
- [ ] Imports organized? (adajoon-conventions)
- [ ] No secrets in code? (adajoon-security)
- [ ] Input validation? (adajoon-security)
- [ ] Database transactions? (adajoon-database)

# For JavaScript changes:
- [ ] const/let (no var)? (adajoon-conventions)
- [ ] Arrow functions? (adajoon-conventions)
- [ ] Async/await not .then()? (adajoon-conventions)
- [ ] XSS prevention? (adajoon-security)
- [ ] CSRF token included? (adajoon-security)

# For deployment:
- [ ] Environment variables set? (adajoon-deployment)
- [ ] Database migrations? (adajoon-database)
- [ ] Health checks work? (adajoon-deployment)
```

### After Deployment

Within 48 hours of deployment, review:

```markdown
## Post-Deployment Review

**Deployment**: v1.2.3 (2026-04-04)
**Changes**: Added channel health filtering

**Questions**:
1. Did it work as expected? ✅ Yes
2. Any unexpected issues? ⚠️ Slow query on large datasets
3. User feedback? ✅ Positive
4. Skills followed? ⚠️ Missing index on health_status column
5. Skill gaps discovered? Yes - need query optimization section

**Actions**:
- [ ] Add index to health_status column
- [ ] Update adajoon-database with index strategy for enum columns
- [ ] Document N+1 query prevention pattern
```

### Weekly Pattern Review

Every Friday, review the week:

```markdown
## Weekly Review: 2026-04-04

**Code Written**: 15 files changed, 847 additions
**PRs Merged**: 7

**Patterns Observed**:
- ✅ Excellent: Type hints used consistently (100%)
- ✅ Good: Async/await usage (95%)
- ⚠️ Needs work: Test coverage on edge cases (60%)
- ❌ Problem: 3 instances of missing input validation

**Skill Violations**:
- adajoon-security: 3x missing validation (channels.py, auth.py, votes.py)
- adajoon-conventions: 2x obvious comments
- adajoon-database: 1x missing transaction

**Next Week Focus**:
1. Add input validation examples to adajoon-security
2. Review all endpoint handlers for validation
3. Create validation helper functions

**Skill Updates Made**: 
- Updated adajoon-security with validation patterns
- Added comment anti-patterns to adajoon-conventions
```

### Monthly Meta-Analysis

First of each month, analyze trends:

```markdown
## Monthly Skill Audit: March 2026

**Stats**:
- Total commits: 134
- Skill violations: 18 (13% of commits)
- Bugs found: 7
- Skills updated: 4

**Which skills are most violated?**
1. adajoon-security (8 violations) - Input validation unclear
2. adajoon-conventions (6 violations) - Comment guidelines vague
3. adajoon-database (4 violations) - Transaction patterns missing

**Which skills prevent most bugs?**
1. adajoon-security (prevented 12 potential vulnerabilities)
2. adajoon-database (prevented 5 data integrity issues)
3. adajoon-conventions (prevented 3 type errors)

**Which skills need clarification?**
- adajoon-security: Add comprehensive input validation section
- adajoon-conventions: More comment anti-pattern examples

**What's missing from our skills?**
- Error handling patterns (create adajoon-error-handling skill?)
- Testing strategies (create adajoon-testing skill?)
- Performance optimization (add to existing skills?)

**Actions**:
- [ ] Expand adajoon-security validation section
- [ ] Add 10 more comment examples to adajoon-conventions
- [ ] Research need for error-handling skill
```

---

## Feedback Loops

### Code Review → Skill Updates

**Process**:
1. Reviewer spots pattern violation
2. Check if skill covers this
3. If missing: Add to skill immediately
4. If unclear: Clarify with example
5. If outdated: Update with new pattern

**Example workflow**:
```markdown
# PR Comment
Found SQL injection vulnerability in search endpoint.

[Action]:
1. ✅ Fix the code in this PR
2. ✅ Check adajoon-security skill - has SQL injection section but no FastAPI examples
3. ✅ Add FastAPI parameterized query example
4. ✅ Update skill version to v1.3
5. ✅ Notify team of skill update
```

### Bug Fixes → Pattern Documentation

**Process**:
1. Bug discovered
2. Root cause analysis
3. Fix implemented
4. Pattern documented in skill
5. Prevention mechanism added

**Template**:
```markdown
## Bug → Skill Update

**Bug**: Race condition in concurrent vote handling
**Root Cause**: Missing database-level locking
**Fix**: Added SELECT FOR UPDATE
**Skill Updated**: adajoon-database
**Section**: "Concurrent Updates"
**Prevention**: Added to code review checklist
**Validation**: Created integration test for concurrent operations
```

### Performance Issues → Best Practices

**Process**:
1. Performance issue identified
2. Profile and measure
3. Optimization implemented
4. Pattern added to skill
5. Benchmark documented

**Example**:
```markdown
## Performance → Skill Update

**Issue**: Channel listing taking 2.5s with 10k channels
**Root Cause**: N+1 query loading categories
**Fix**: Added joinedload for eager loading
**Measurement**: Reduced to 150ms (94% improvement)
**Skill Updated**: adajoon-database v1.4
**Section**: Added "Query Optimization" with joinedload examples
**Rule Added**: Always use joinedload for known relationships
```

### Security Incidents → Immediate Updates

**Process** (highest priority):
1. Incident detected
2. Immediate fix deployed
3. Skill updated within 24 hours
4. Team notified of update
5. Audit codebase for similar issues

**Template**:
```markdown
## SECURITY INCIDENT → SKILL UPDATE

**Incident**: API key exposed in client-side code
**Severity**: CRITICAL
**Impact**: Potential unauthorized access
**Immediate Fix**: Rotated keys, moved to server-side only
**Skill Updated**: adajoon-security v2.0 (MAJOR)
**Changes**:
- Added "Never expose API keys in frontend" rule
- Added pre-commit hook to scan for common key patterns
- Added checklist item: "Verify no secrets in frontend bundle"
**Audit**: Scanned entire codebase - found 2 more instances, fixed
**Prevention**: Added .env.example with dummy values
**Team Notified**: 2026-04-04 via Slack + email
```

---

## Skill Evolution

### Versioning Skills

Use semantic versioning for skills:

**Format**: `vMAJOR.MINOR.PATCH`

- **MAJOR**: Breaking change (old pattern deprecated, incompatible)
- **MINOR**: New pattern added (backward compatible)
- **PATCH**: Clarification, typo, example improvement

**Version header** (add to skill file):
```markdown
---
name: adajoon-security
version: 2.1.3
last_updated: 2026-04-04
description: ...
---

# Adajoon Security

**Version**: 2.1.3 (Updated: 2026-04-04)

## Changelog
- v2.1.3 (2026-04-04): Added CORS configuration examples
- v2.1.0 (2026-03-15): Added rate limiting patterns
- v2.0.0 (2026-03-01): Deprecated basic auth, mandate OAuth/passkeys
- v1.5.2 (2026-02-10): Clarified input validation for JSON bodies
```

### Track Changes and Why

For each skill update, document rationale:

```markdown
## Skill Update Record

**Skill**: adajoon-database
**Version**: 1.3.0 → 1.4.0
**Date**: 2026-04-04
**Type**: MINOR (new pattern added)

**Changes**:
- Added "Query Optimization" section
- Added joinedload examples
- Added N+1 query prevention

**Why**:
- Had 3 performance issues in last month due to N+1 queries
- Team unfamiliar with SQLAlchemy eager loading
- Real performance impact: 2.5s → 150ms on channel listing

**Evidence**:
- PR #234: Channel listing optimization
- PR #241: Category loading fix
- PR #256: User profile N+1 fix

**Success Metrics**:
- Track N+1 queries in next 30 days (expect 0)
- Measure if team uses joinedload in new code
- Check if performance issues related to queries decrease
```

### A/B Test Patterns

For controversial patterns, test before mandating:

```markdown
## Pattern A/B Test

**Pattern**: Auto-format on save vs. pre-commit hook
**Duration**: 2 weeks (Mar 1-14, 2026)
**Team Split**: 
- Team A (3 devs): Auto-format on save
- Team B (3 devs): Pre-commit hook only

**Hypothesis**: Auto-format reduces formatting PRs and cognitive load

**Metrics**:
- Formatting-only commits
- Developer reported friction
- Time spent on style discussions

**Results**:
- Team A: 2 formatting commits, "feels seamless"
- Team B: 14 formatting commits, "annoying to fix before commit"
- Style discussions: A=0, B=5

**Conclusion**: ✅ Adopt auto-format on save
**Skill Updated**: adajoon-conventions
**Added**: "Use format-on-save in VSCode/Cursor settings"
```

### Deprecate Outdated Patterns

When patterns become obsolete, deprecate gracefully:

```markdown
## Pattern Deprecation

**Pattern**: Using os.getenv() directly in route handlers
**Reason**: Inconsistent, hard to test, no type safety
**Better Pattern**: Centralized settings object
**Timeline**: 
- 2026-03-01: Mark as deprecated in skill
- 2026-03-15: Add migration guide
- 2026-04-01: Remove from skill (keep in "Old Patterns" section)

**Migration Guide**:
\`\`\`python
# ❌ OLD (deprecated)
API_KEY = os.getenv("API_KEY")

# ✅ NEW (use settings object)
from app.config import settings
API_KEY = settings.api_key
\`\`\`

**Skill Update**:
```markdown
## Configuration (Updated v1.5.0)

Use settings object, not `os.getenv()` in application code.

<details>
<summary>Old Pattern (Deprecated - Remove by April 2026)</summary>

\`\`\`python
# This pattern is deprecated
API_KEY = os.getenv("API_KEY")
\`\`\`
</details>
```
```

---

## Meta-Learning

### Violation Analysis

Run monthly to identify systemic issues:

```bash
# Analyze skill violations from weekly reviews
cat .cursor/skills/adajoon-skill-improvement/logs/violations.md | \
  awk '{print $2}' | sort | uniq -c | sort -rn

# Output:
#   12 adajoon-security
#    8 adajoon-conventions
#    4 adajoon-database
#    2 adajoon-frontend

# Interpretation:
# - Security skill violated most → needs clarification or better examples
# - Check which security rules are violated (likely input validation)
```

**Template for tracking**:
```markdown
## Violation Tracking

### 2026-03 Summary
| Skill | Violations | Top Reason | Action Taken |
|-------|------------|-----------|--------------|
| adajoon-security | 12 | Missing input validation | Added validation examples v2.1.0 |
| adajoon-conventions | 8 | Obvious comments | Added 10 anti-pattern examples v1.4.1 |
| adajoon-database | 4 | Missing transactions | Added transaction guide v1.3.2 |
```

### Bug Prevention Metrics

Track which skills prevent bugs:

```markdown
## Bug Prevention Analysis

**Period**: Q1 2026
**Total Bugs**: 23

**Bugs Prevented by Skills**:
| Skill | Bugs Prevented | Examples |
|-------|----------------|----------|
| adajoon-security | 15 | Input validation, SQL injection, XSS |
| adajoon-database | 6 | Transaction issues, race conditions |
| adajoon-conventions | 2 | Type errors caught by hints |

**Bugs That Slipped Through**:
| Bug | Why Skill Didn't Catch | Fix |
|-----|------------------------|-----|
| Incorrect date calculation | No date handling skill | Add temporal patterns to conventions |
| Memory leak in WebSocket | No async cleanup guide | Add to deployment skill |
| Race in cache invalidation | No caching patterns | Create caching skill? |

**ROI Calculation**:
- Time spent updating skills: ~4 hours/month
- Bugs prevented: ~20/month
- Avg bug fix time: 2 hours
- Time saved: 40 hours/month
- **ROI**: 10x
```

### Clarity Analysis

Survey or observe which skills cause confusion:

```markdown
## Skill Clarity Report

**Method**: Analyzed PR comments asking for clarification

**Confusing Areas** (Mar 2026):
1. adajoon-security "input validation" (7 questions)
   - "What counts as user input?"
   - "Do I validate query params?"
   - "Where to validate: route or service?"
   
2. adajoon-conventions "non-obvious comments" (5 questions)
   - "Is this comment obvious?"
   - "Should I explain this algorithm?"

**Actions**:
- [ ] Add "What to Validate" section to security skill
- [ ] Add decision tree: route vs service validation
- [ ] Add 20 examples to comment guidelines (10 good, 10 bad)
- [ ] Create flowchart: "Should I add this comment?"
```

### Gap Analysis

What patterns are we missing?

```markdown
## Skill Gap Analysis

**Method**: Review all PRs from last quarter for patterns not in skills

**Undocumented Patterns** (found in code but not in skills):
1. **Error handling** (appears in 45 files)
   - Try/except patterns
   - Custom exception classes
   - Error logging
   - User-facing error messages
   → **Action**: Create adajoon-error-handling skill

2. **Testing** (appears in 32 test files)
   - Test structure
   - Fixtures
   - Mocking external services
   - Integration test patterns
   → **Action**: Create adajoon-testing skill

3. **Caching** (appears in 12 files)
   - Redis patterns
   - Cache invalidation
   - TTL strategies
   → **Action**: Add caching section to adajoon-backend skill

4. **Background jobs** (appears in 8 files)
   - Celery task patterns
   - Retry strategies
   - Error handling
   → **Action**: Create adajoon-background-jobs skill when more patterns emerge

**Prioritization**:
1. Error handling (high frequency, high impact)
2. Testing (medium frequency, high impact)
3. Caching (low frequency, high impact)
4. Background jobs (low frequency, defer until more patterns)
```

---

## Templates

### Deviation Log Template

Create: `.cursor/skills/adajoon-skill-improvement/logs/deviations.md`

```markdown
# Skill Deviation Log

Track when code deviates from established skills.

---

## [YYYY-MM-DD] Skill Name - Brief Description

**Date**: YYYY-MM-DD
**Skill**: skill-name
**Deviation**: What was done differently
**Location**: `path/to/file.py:line`
**Impact**: Critical/High/Medium/Low
**Root Cause**: Why it happened
**Fix**: What was done to correct it
**Skill Update**: What changed in the skill (if any)

---
```

### Pattern Effectiveness Template

Create: `.cursor/skills/adajoon-skill-improvement/logs/patterns.md`

```markdown
# Pattern Effectiveness Log

Track which patterns work in practice vs which don't.

---

## Pattern: [Name]

**Skill**: skill-name
**Status**: ✅ WORKING | ⚠️ NEEDS CLARITY | ❌ NOT WORKING
**Evidence**: Data points showing adoption/effectiveness
**Notes**: Observations and recommendations

---
```

### Learning Entry Template

Create: `.cursor/skills/adajoon-skill-improvement/learnings/YYYY-MM-DD-issue-number.md`

```markdown
# Learning Entry #NNN

**Date**: YYYY-MM-DD
**Category**: Database | Security | API | Frontend | Deployment
**Issue**: Brief description

## What Happened
Detailed description of the problem.

## Why It Happened
Root cause analysis.

## The Fix
\`\`\`language
code showing the fix
\`\`\`

## Skill Update
- **Skill**: skill-name
- **Section**: Section name
- **Change**: What was added/modified
- **Version**: New version number

## Prevention
How we prevent this in the future.
```

### Weekly Review Template

Create: `.cursor/skills/adajoon-skill-improvement/reviews/YYYY-MM-DD-weekly.md`

```markdown
# Weekly Review: YYYY-MM-DD

## Stats
- Code written: X files changed, Y additions, Z deletions
- PRs merged: N
- Bugs found: M

## Patterns Observed
- ✅ Excellent: [Pattern name] (X%)
- ✅ Good: [Pattern name] (X%)
- ⚠️ Needs work: [Pattern name] (X%)
- ❌ Problem: [Issue description]

## Skill Violations
- skill-name: Nx [brief reason]
- skill-name: Nx [brief reason]

## Next Week Focus
1. Priority 1
2. Priority 2
3. Priority 3

## Skill Updates Made
- Updated skill-name with [change]
- Added [pattern] to skill-name
```

### Monthly Audit Template

Create: `.cursor/skills/adajoon-skill-improvement/audits/YYYY-MM-monthly.md`

```markdown
# Monthly Skill Audit: [Month Year]

## Stats
- Total commits: N
- Skill violations: N (X% of commits)
- Bugs found: N
- Skills updated: N

## Which skills are most violated?
1. skill-name (N violations) - Reason
2. skill-name (N violations) - Reason

## Which skills prevent most bugs?
1. skill-name (prevented N issues)
2. skill-name (prevented N issues)

## Which skills need clarification?
- skill-name: What needs clarification

## What's missing from our skills?
- Gap 1
- Gap 2

## Actions
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

## Metrics
- Skill adoption rate: X%
- Bug prevention rate: Y%
- Time spent on skill updates: Z hours
- Estimated time saved: W hours
- ROI: Nx
```

---

## Implementation Checklist

To start using this skill:

### Initial Setup
- [ ] Create `.cursor/skills/adajoon-skill-improvement/` directory
- [ ] Create `logs/` subdirectory for deviation and pattern logs
- [ ] Create `learnings/` subdirectory for bug learnings
- [ ] Create `reviews/` subdirectory for weekly reviews
- [ ] Create `audits/` subdirectory for monthly audits
- [ ] Initialize template files from this skill

### Establish Rhythm
- [ ] Set Friday reminder for weekly review
- [ ] Set first-of-month reminder for monthly audit
- [ ] Add "Check skills" step to PR template
- [ ] Add skill update process to bug fix template

### Add Version Headers
- [ ] Add version and changelog to each existing skill
- [ ] Use semantic versioning (vMAJOR.MINOR.PATCH)
- [ ] Start all skills at v1.0.0

### Create Tracking System
- [ ] Set up violation tracking spreadsheet or doc
- [ ] Create bug prevention metrics dashboard
- [ ] Document skill update approval process (if needed)

---

## Success Metrics

Track these to measure skill effectiveness:

### Leading Indicators (predict future quality)
- Skill violation rate (target: <5% of commits)
- Time from violation to skill update (target: <7 days)
- Number of skill updates per month (target: 2-4)

### Lagging Indicators (measure actual quality)
- Bugs prevented by skills (track via close calls)
- Bug recurrence rate (same type of bug) (target: <10%)
- Time spent fixing skill-preventable issues (target: decreasing)

### Process Metrics
- Weekly review completion rate (target: 100%)
- Monthly audit completion rate (target: 100%)
- Team engagement with skills (track via PR comments)

---

## Quick Reference

### Daily
- Note deviations as you spot them
- Log patterns that work/fail

### Weekly (Friday)
- Review week's code and PRs
- Update skill violation log
- Make small skill clarifications
- Run weekly review template

### Monthly (1st of month)
- Analyze violation patterns
- Measure bug prevention
- Identify skill gaps
- Update skills based on trends
- Run monthly audit template

### As Needed
- After incidents: Update skills immediately
- Before major features: Review relevant skills
- After retrospectives: Document learnings
- When confused: Clarify skill

---

## Advanced: Automated Tracking

Consider automating metric collection:

```python
# Example: Count skill violations in PR comments
import re
from github import Github

def count_skill_violations(repo_name, since_date):
    g = Github(token)
    repo = g.get_repo(repo_name)
    pulls = repo.get_pulls(state='all', sort='created', direction='desc')
    
    violations = {}
    for pr in pulls:
        if pr.created_at < since_date:
            break
        for comment in pr.get_issue_comments():
            matches = re.findall(r'\[SKILL:([^\]]+)\]', comment.body)
            for skill in matches:
                violations[skill] = violations.get(skill, 0) + 1
    
    return violations

# Run monthly and feed into audit template
```

```bash
# Example: Pre-commit hook to remind about skills
#!/bin/bash
# .git/hooks/pre-commit

echo "🎯 Remember to check relevant skills:"
git diff --cached --name-only | while read file; do
  case "$file" in
    backend/*) echo "  - adajoon-backend, adajoon-security, adajoon-database" ;;
    frontend/*) echo "  - adajoon-frontend, adajoon-security" ;;
    *.md) echo "  - adajoon-conventions (commit message)" ;;
  esac
done | sort -u
```

---

## Conclusion

Skill improvement is not a one-time task but a continuous process.

**Key principles**:
1. **Document everything** - Deviations, patterns, learnings
2. **Review regularly** - Weekly patterns, monthly trends
3. **Update quickly** - Don't let outdated skills linger
4. **Measure impact** - Know what works
5. **Iterate fast** - Small frequent updates beat big rewrites

The goal: Skills that evolve with your codebase and prevent tomorrow's bugs based on today's learnings.
