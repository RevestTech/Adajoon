# Getting Started with Skill Improvement

Follow this checklist to begin systematic skill improvement today.

## ✅ Immediate Setup (5 minutes)

- [x] Skill directory created: `.cursor/skills/adajoon-skill-improvement/`
- [x] Templates created for tracking
- [x] Version headers added to all existing skills
- [ ] Read the main [SKILL.md](SKILL.md) file (10 min read)
- [ ] Skim the [README.md](README.md) for quick reference

## ✅ This Week (First Actions)

### Today
- [ ] Create `logs/quick-notes.txt` and start jotting down observations
- [ ] Next time you review code, try tagging skill violations: `[SKILL:adajoon-security] Missing validation`
- [ ] If you fix a bug today, copy `learnings/example-learning.md` and document it

### Friday (First Weekly Review)
- [ ] Copy `reviews/weekly-template.md` to `reviews/2026-04-04-weekly.md`
- [ ] Spend 15-20 minutes filling it out based on this week's work
- [ ] Identify 1-3 patterns that need attention
- [ ] Update a skill if something was unclear

## ✅ This Month

### Week 1
- [x] System setup complete
- [ ] First weekly review done

### Week 2-4
- [ ] Continue weekly reviews
- [ ] Document at least 2 learnings
- [ ] Track deviation patterns

### End of Month (First Monthly Audit)
- [ ] Copy `audits/monthly-template.md` to `audits/2026-04-monthly.md`
- [ ] Aggregate data from 4 weekly reviews
- [ ] Calculate ROI (rough estimate is fine)
- [ ] Identify top 3 priorities for next month

## 🎯 Quick Wins to Try First

### 1. Tag Skill Violations in PRs
When reviewing code, instead of:
```
"You should validate user input here"
```

Try:
```
[SKILL:adajoon-security] Missing input validation on user_id parameter.
See the "Input Validation" section for patterns.
```

**Why**: Makes skill violations trackable and measurable.

### 2. Document Your Next Bug Fix
Next time you fix a bug:
1. Copy `learnings/example-learning.md`
2. Fill it out (5 minutes)
3. Update the relevant skill if needed

**Why**: Prevents the same bug from recurring.

### 3. Keep a Quick Notes File
```bash
# Create the file
touch .cursor/skills/adajoon-skill-improvement/logs/quick-notes.txt

# Add notes throughout the week
echo "2026-04-04: Great type hints in PR #245" >> logs/quick-notes.txt
echo "2026-04-04: Missing transaction in user_service.py" >> logs/quick-notes.txt
echo "2026-04-05: Team confused about when to use async" >> logs/quick-notes.txt
```

**Why**: Makes weekly reviews 10x easier when you have notes.

## 📊 Success Metrics (Check Monthly)

Track these simple metrics to show value:

### Easy to Track
- [ ] Number of skill violations per week (from PR comments)
- [ ] Number of skill updates made
- [ ] Bugs documented in learnings/

### Medium Effort
- [ ] Estimated bugs prevented (track "close calls" in code reviews)
- [ ] Time spent on repetitive corrections (decreasing?)
- [ ] Questions about skill clarity (track PR discussions)

### Nice to Have
- [ ] Calculate ROI: `(Bugs Prevented × Avg Fix Time) / Time Spent on Skills`
- [ ] Team engagement: Count `[SKILL:*]` tags in PR comments

## 🚀 Leveling Up (After First Month)

Once you're comfortable with weekly reviews:

### Add Automation
```bash
# Pre-commit hook to remind about skills
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🎯 Remember to check relevant skills:"
git diff --cached --name-only | while read file; do
  case "$file" in
    backend/*) echo "  - adajoon-backend, adajoon-security" ;;
    frontend/*) echo "  - adajoon-frontend" ;;
  esac
done | sort -u
EOF
chmod +x .git/hooks/pre-commit
```

### Create Violation Dashboard
```bash
# Count skill violations by type
grep -r "\[SKILL:" ../../../ --include="*.md" | \
  sed 's/.*\[SKILL:\([^]]*\)\].*/\1/' | \
  sort | uniq -c | sort -rn > logs/violation-summary.txt
```

### Team Integration
- [ ] Add skill improvement item to sprint retrospectives
- [ ] Share interesting learnings in team meetings
- [ ] Celebrate when skills prevent bugs

## ⚡ Power User Tips

### For Code Reviews
Create a review checklist template:
```markdown
## Code Review Checklist

**Skills Applied**:
- [ ] adajoon-conventions (naming, formatting, comments)
- [ ] adajoon-security (auth, validation, secrets)
- [ ] adajoon-backend (routing, caching, logging)
- [ ] adajoon-database (queries, migrations, transactions)

**Violations Found**: [SKILL:*] tags used in comments

**Patterns Noticed**: Add to quick-notes.txt
```

### For Bug Fixes
Template for commit messages:
```
fix(votes): prevent race condition in concurrent voting

Used SELECT FOR UPDATE to lock during check-then-insert.

Skill updated: adajoon-database v1.3.0 → v1.4.0
Learning documented: learnings/2026-04-04-vote-race-condition.md
```

### For Skill Updates
Before updating a skill, check:
1. Is this a pattern (3+ occurrences) or one-off?
2. Do we have evidence it works?
3. Is it general enough for the skill?
4. Have we tested it in real code?

## 🆘 Troubleshooting

### "Weekly reviews take too long"
- Use `logs/quick-notes.txt` throughout the week
- Set a 20-minute timer and stop when it goes off
- Focus on patterns, not every single PR
- Templates are guides, not forms to fill completely

### "Not seeing value"
- Check: Are you tracking violations with [SKILL:*] tags?
- Check: Have you documented any learnings?
- Check: Are weekly reviews actually happening?
- Try: Focus on one high-impact skill (probably security)

### "Team isn't engaging"
- Start with yourself - lead by example
- Share interesting findings in standups
- Make it lightweight - just the [SKILL:*] tags
- Show ROI data from monthly audits

### "Skills becoming outdated"
- Good! That means you're learning
- Deprecate old patterns (don't delete)
- Version updates show skill evolution
- Use changelog to explain why changes happened

## 📚 Reference

### Key Files
- **SKILL.md**: Complete methodology and patterns
- **README.md**: Quick reference and overview
- **logs/deviations.md**: Track skill violations
- **logs/patterns.md**: Track pattern effectiveness
- **learnings/**: Document bugs and fixes
- **reviews/**: Weekly review history
- **audits/**: Monthly audit history

### Versioning
All skills now use semantic versioning:
- **MAJOR** (v2.0.0): Breaking change, old pattern deprecated
- **MINOR** (v1.1.0): New pattern added
- **PATCH** (v1.0.1): Clarification, example, typo fix

### Templates
Copy these files to create new entries:
- `reviews/weekly-template.md` → `reviews/YYYY-MM-DD-weekly.md`
- `audits/monthly-template.md` → `audits/YYYY-MM-monthly.md`
- `learnings/example-learning.md` → `learnings/YYYY-MM-DD-description.md`

## 🎓 Learning Resources

### Karpathy-Style Learning
This skill is inspired by Andrej Karpathy's approach:
1. **Learn by doing**: Skills improve through real implementation
2. **Track everything**: Deviations, patterns, what works/doesn't
3. **Iterate fast**: Small updates beat large rewrites
4. **Build understanding**: Document why, not just what
5. **Test assumptions**: Validate patterns with real code

### Feedback Loop Philosophy
```
Code → Observe → Document → Update Skill → Code Better → Repeat
```

Each cycle makes skills more effective. The goal isn't perfection - it's continuous improvement.

## ✨ Your First Week Plan

### Monday
- Read SKILL.md and README.md
- Create `logs/quick-notes.txt`
- Start noting patterns as you code

### Tuesday-Thursday
- Tag skill violations in code reviews: `[SKILL:*]`
- Add observations to quick-notes.txt
- If you fix a bug, document it in learnings/

### Friday (15 minutes)
- Copy weekly-template.md
- Review your quick-notes.txt
- Fill out the template
- Identify 1-3 priorities for next week
- Update a skill if needed (5 min max)

### Next Week
- Repeat with slightly more confidence
- Notice patterns emerging
- Skills starting to prevent issues

---

**Remember**: Start small. The system works best when it's a habit, not a project.

**First action**: Create `logs/quick-notes.txt` and add your first observation right now. 🚀
