# Learning Entries

Document mistakes, bugs, and their fixes to prevent recurrence.

## File Naming Convention

`YYYY-MM-DD-brief-description.md`

Examples:
- `2026-04-04-race-condition-votes.md`
- `2026-04-05-sql-injection-search.md`
- `2026-04-10-missing-transaction-update.md`

## Template

Use this template for each learning entry:

```markdown
# Learning Entry: [Brief Title]

**Date**: YYYY-MM-DD
**Category**: Database | Security | API | Frontend | Deployment | Performance
**Related PR/Issue**: #123

## What Happened
Detailed description of the problem or bug.

## Why It Happened
Root cause analysis. What was missing or misunderstood?

## The Fix
\`\`\`language
# Show the actual fix with code
async def fixed_function():
    # Fixed implementation
    pass
\`\`\`

## Skill Update
- **Skill**: adajoon-[name]
- **Version**: Old → New (e.g., v1.2.0 → v1.3.0)
- **Section**: Section name that was updated
- **Change**: What was added or modified in the skill

## Prevention
How we prevent this in the future:
- [ ] Updated skill with pattern
- [ ] Added to code review checklist
- [ ] Created test to catch similar issues
- [ ] Shared with team

## Related Learnings
Link to similar past issues or patterns.
```

## Example Entry

See `example-learning.md` for a complete example.
