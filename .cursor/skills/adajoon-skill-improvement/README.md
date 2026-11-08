# Adajoon Skill Improvement System

A systematic approach to evolving Cursor skills through continuous learning and iteration, inspired by Andrej Karpathy's learning methodologies.

## Quick Start

### 1. When to Use This Skill

The skill improvement process triggers automatically during:
- Code reviews
- Bug fixes and postmortems
- Retrospectives
- When you notice repetitive corrections

Or manually invoke by mentioning:
- "improve skills"
- "update guidelines"
- "skill feedback"
- "document this pattern"

### 2. Daily Practice

**As you code, take quick notes:**
```bash
# Spot a deviation from a skill?
echo "2026-04-04: Missing input validation in channels.py:45" >> logs/quick-notes.txt

# Pattern working well?
echo "✅ async/await usage perfect in last 10 PRs" >> logs/quick-notes.txt

# Something confusing?
echo "⚠️ Team asked 3x about when to use transactions" >> logs/quick-notes.txt
```

### 3. Weekly Review (Fridays)

**Time required:** 15-20 minutes

1. Copy `reviews/weekly-template.md` to `reviews/2026-04-04-weekly.md`
2. Fill in the template based on the week's activity
3. Identify top 3 priorities for next week
4. Update skills if needed (minor clarifications)

### 4. Monthly Audit (First of Month)

**Time required:** 30-45 minutes

1. Copy `audits/monthly-template.md` to `audits/2026-04-monthly.md`
2. Analyze trends from weekly reviews
3. Calculate ROI metrics
4. Plan major skill updates
5. Identify skill gaps

## Directory Structure

```
adajoon-skill-improvement/
├── SKILL.md                      # Main skill documentation
├── README.md                     # This file
├── logs/
│   ├── deviations.md            # Track skill violations
│   ├── patterns.md              # Track pattern effectiveness
│   └── quick-notes.txt          # Daily observations
├── learnings/
│   ├── README.md                # Learning entry guide
│   ├── example-learning.md      # Example bug analysis
│   └── YYYY-MM-DD-*.md          # Individual learnings
├── reviews/
│   ├── weekly-template.md       # Copy for each weekly review
│   └── YYYY-MM-DD-weekly.md     # Completed reviews
└── audits/
    ├── monthly-template.md      # Copy for each monthly audit
    └── YYYY-MM-monthly.md       # Completed audits
```

## Current Skill Versions

| Skill | Version | Last Updated | Status |
|-------|---------|--------------|--------|
| adajoon-conventions | v1.0.0 | 2026-04-04 | ✅ Active |
| adajoon-security | v1.0.0 | 2026-04-04 | ✅ Active |
| adajoon-backend | v1.0.0 | 2026-04-04 | ✅ Active |
| adajoon-frontend | v1.0.0 | 2026-04-04 | ✅ Active |
| adajoon-database | v1.0.0 | 2026-04-04 | ✅ Active |
| adajoon-deployment | v1.0.0 | 2026-04-04 | ✅ Active |
| adajoon-skill-improvement | v1.0.0 | 2026-04-04 | ✅ Active |

## Common Workflows

### After Finding a Bug

1. **Fix the bug** in the code
2. **Document the learning**:
   ```bash
   # Create learning entry
   cp learnings/example-learning.md learnings/2026-04-04-vote-race-condition.md
   # Edit with details about the bug, fix, and root cause
   ```
3. **Update the relevant skill** if it's missing the pattern
4. **Add to code review checklist** if it should be caught in reviews

### After Code Review Finds Pattern Violation

1. **Note the violation**:
   ```markdown
   # In logs/deviations.md
   ## 2026-04-04: Missing CSRF Protection
   
   **Skill**: adajoon-security
   **Location**: `backend/app/routers/votes.py:45`
   **Fix**: Added `_csrf: None = Depends(verify_csrf_token)`
   ```
2. **Check if skill needs clarification** - If this is the 3rd time, probably yes
3. **Update skill if needed** with better examples or checklist item

### When a Pattern Isn't Working

1. **Document in patterns log**:
   ```markdown
   # In logs/patterns.md
   ## Pattern: Only comment non-obvious intent
   
   **Status**: ⚠️ NEEDS CLARITY
   **Evidence**: 4 PRs this month had disputes about "obvious"
   **Notes**: Need concrete decision framework
   ```
2. **Discuss with team** if it's a team-wide issue
3. **Update skill** with clarifications or examples
4. **Consider A/B testing** alternative approaches

## Integration with Development Workflow

### Pre-Commit

Before committing, mentally run through relevant skill checklists:
- Writing backend code? → adajoon-backend, adajoon-security, adajoon-database
- Writing frontend code? → adajoon-frontend, adajoon-security
- Changing schemas? → adajoon-database
- Deploying? → adajoon-deployment

### Code Review

When reviewing code, explicitly call out skill violations:
```markdown
# In PR comment
[SKILL:adajoon-security] Missing input validation on user_id parameter. 
See adajoon-security section on input validation.
```

This helps:
- Track which skills need clarification
- Educate the team on existing skills
- Measure skill effectiveness

### Bug Triage

When triaging bugs, ask:
- Would following our skills have prevented this?
- If yes: Was the skill unclear? Add examples.
- If no: Should we add a new pattern to a skill?

## Metrics to Track

### Leading Indicators (Week-to-Week)
- Skill violation rate
- Questions about skill clarity
- Time from violation to skill update

### Lagging Indicators (Month-to-Month)
- Bugs prevented by skills
- Bug recurrence rate
- Time spent on skill-preventable issues

### Process Health
- Weekly review completion
- Monthly audit completion
- Team engagement with skills (PR comments with [SKILL:*])

## Getting Started Checklist

- [x] Skill improvement skill created
- [x] Directory structure established
- [x] Templates created
- [x] Version tracking added to all skills
- [ ] Schedule Friday weekly review reminder
- [ ] Schedule first-of-month audit reminder
- [ ] Add [SKILL:*] format to PR template
- [ ] Share skill improvement process with team
- [ ] Complete first weekly review
- [ ] Complete first monthly audit

## Tips for Success

### Make It a Habit
- Weekly reviews should be routine, like sprint planning
- Don't skip them - the data compounds over time
- 15 minutes every Friday is better than 2 hours once a quarter

### Don't Overthink It
- Notes can be rough - refine during weekly review
- Not every deviation needs a skill update
- Focus on patterns, not one-off issues

### Involve the Team
- Share weekly review findings in standups
- Get team input on skill clarity issues
- Celebrate when skills prevent bugs

### Iterate Quickly
- Small, frequent skill updates beat large rewrites
- Add examples when patterns are unclear
- Remove or deprecate patterns that don't work

### Measure Impact
- Track bugs prevented (rough estimates are fine)
- Calculate ROI monthly to justify time investment
- Share success stories with the team

## Questions?

This is a meta-skill - it's designed to improve itself! If you find:
- This process is too heavy → Simplify templates
- You're not getting value → Focus on high-ROI activities
- Team isn't engaging → Make it more lightweight

Document these observations and update the skill improvement skill itself.

## Next Steps

1. **This Week**: Start taking daily notes in `logs/quick-notes.txt`
2. **This Friday**: Complete your first weekly review
3. **Next Month**: Complete your first monthly audit
4. **Ongoing**: Update skills as patterns emerge

Remember: The goal is continuous improvement, not perfection. Start small, iterate, and let the system evolve with your team's needs.
