# Quick Start: Create Skills for Any Project (30-Minute Version)

**For AI Agents**: This is the condensed version. For comprehensive guide, see `CREATE-SKILLS-FOR-ANY-PROJECT.md`.

---

## What You'll Create

A skill system that works in Cursor Agent, Cursor Composer/Chat, and direct Claude conversations.

**Time Investment**: 30-60 minutes initial, 15 min/week maintenance

---

## Step 1: Analyze (10 minutes)

### ⚠️ CRITICAL: Understand YOUR Project First

**Don't create generic skills! Extract actual patterns from THIS codebase.**

#### Check Project Type

**Company Project?**
- Look for existing company style guides/rules
- Include compliance/regulatory requirements
- Follow company branding/terminology

**Private Project?**
- Focus on technical patterns and architecture
- Team/individual conventions

**Open Source?**
- Contributor guidelines, API stability, documentation

#### Quick Analysis Commands

```bash
# What type of project is this?
ls -la  # Check root directory
cat README.md | head -20  # Project description

# Existing rules?
find . -name "*STYLE*" -o -name "*GUIDE*" -o -name ".cursorrules" | head -10

# What tech is actually used?
find . -name "package.json" -o -name "requirements.txt" -o -name "go.mod" | head -5

# What's the actual structure?
ls -d backend/ frontend/ src/ api/ components/ 2>/dev/null
```

#### Identify Technical Areas (Based on Actual Code)

**For Company Project:**
```
1. Company style guide (FIRST - foundation for others)
2. Backend API
3. Frontend
4. Security + Compliance
5. Database
6. Deployment
7. Conventions
```

**For Private Project:**
```
1. Backend/API
2. Frontend  
3. Database
4. Security
5. Deployment
6. Conventions
```

**Adjust based on what YOUR project actually has!**

---

## Step 2: Create Skills (15-30 minutes)

### Option A: Sequential (30 minutes)

Create one skill at a time using this prompt template:

```
Analyze [directory path] and create a skill at .cursor/skills/[project]-[area]/SKILL.md

Extract patterns for:
- File/folder structure
- Naming conventions
- Common code patterns
- Error handling
- [area-specific patterns]

Format: 300-500 lines with:
- Version: 1.0.0
- Code examples from actual codebase
- Anti-patterns to avoid
- Quick reference checklist
- Common mistakes section

Use template from [paste template or reference]
```

### Option B: Parallel (15 minutes)

Launch multiple agents at once:

```
Launch 3-6 agents in parallel to create skills:

Agent 1: [project]-backend skill from [backend path]
Agent 2: [project]-frontend skill from [frontend path]  
Agent 3: [project]-security skill from [auth/security files]
Agent 4: [project]-database skill from [models/migrations path]
Agent 5: [project]-deployment skill from [Dockerfile, CI/CD files]
Agent 6: [project]-conventions skill from [entire codebase]

Each should be 300-500 lines with real code examples.
```

---

## Step 3: Create Unified Access (10 minutes)

### Create .cursorrules (Project Root)

```bash
# Prompt:
Create a .cursorrules file (200-300 lines) that summarizes all skills.

Include:
- Core principles (5-10 rules)
- Quick patterns for each skill area
- File-specific triggers
- Common anti-patterns

Keep it concise - this loads on every Cursor interaction.
```

### Create CLAUDE.md

```bash
# Prompt:
Create .cursor/skills/CLAUDE.md (800-1000 lines) consolidating all skills.

Include:
- Quick jump navigation
- All patterns from individual skills (consolidated)
- Common scenarios section (10-15 examples)
- Pattern quick reference table

This is for @ mentions and copy/paste reference.
```

### Update README.md

Add this section to your main README:

```markdown
## Using Skills

### Cursor Agent Mode
Just code - skills auto-apply! ✨

### Cursor Composer/Chat  
```bash
@.cursor/skills/CLAUDE.md how do I [task]?
```

### Direct Claude
1. Open `.cursor/skills/CLAUDE.md`
2. Search for topic (Cmd/Ctrl+F)
3. Copy relevant section
```

---

## Step 4: Add Continuous Improvement (5 minutes)

Create basic tracking structure:

```bash
mkdir -p .cursor/skills/[project]-skill-improvement/{logs,learnings,reviews}

echo "# Quick Notes" > .cursor/skills/[project]-skill-improvement/logs/quick-notes.txt
```

Add observations as you code:

```txt
2026-04-04: ✅ Auth pattern worked well
2026-04-04: ⚠️ Forgot CSRF token - need checklist
```

---

## Step 5: Commit (2 minutes)

```bash
git add .cursor/ .cursorrules README.md
git commit -m "feat: add skill system with [N] skills

Created skills for:
- [skill 1]
- [skill 2]
- [...]

Includes:
- .cursorrules for Cursor built-in system
- CLAUDE.md for @ mentions and copy/paste
- Individual SKILL.md files with patterns

~[X,XXX] lines of guidelines"

git push
```

---

## Essential Skill Template

Minimum viable skill:

```markdown
# [Project] [Area] Patterns

**Version**: 1.0.0  
**Triggers**: When working with [file patterns]

## Core Patterns

### Pattern 1: [Name]
```[language]
// Example from codebase
```

**When to use**: [description]  
**Key points**:
- Point 1
- Point 2

### Pattern 2: [Name]
[...]

## Anti-Patterns

❌ **Don't do this:**
```[language]
// Bad example
```

✅ **Do this instead:**
```[language]
// Good example
```

## Quick Checklist

When [creating/reviewing] [code type]:
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## Common Mistakes

1. **Mistake**: [description]
   - **Fix**: [solution]

## Examples from Codebase

### Example 1
```[language]
// Real code showing pattern
```

**Why this works**: [explanation]
```

---

## Parallel Agent Prompt (Copy/Paste Ready)

```
Create a comprehensive skill system for my project.

PROJECT INFO:
- Name: [project name]
- Tech stack: [backend tech], [frontend tech], [database], [deployment]
- Main directories: [list key paths]

TASK:
Launch 6 agents in parallel to create skills:

Agent 1 - Backend Skill:
- Analyze: [backend path]
- Create: .cursor/skills/[project]-backend/SKILL.md
- Extract patterns for: routing, auth, error handling, API structure
- Include real code examples from the codebase
- 400-500 lines

Agent 2 - Frontend Skill:
- Analyze: [frontend path]
- Create: .cursor/skills/[project]-frontend/SKILL.md
- Extract patterns for: components, state, API calls, routing
- Include real code examples from the codebase
- 400-500 lines

Agent 3 - Security Skill:
- Analyze: [auth/security files]
- Create: .cursor/skills/[project]-security/SKILL.md
- Extract patterns for: authentication, authorization, input validation, headers
- Include real code examples from the codebase
- 400-500 lines

Agent 4 - Database Skill:
- Analyze: [models/migrations path]
- Create: .cursor/skills/[project]-database/SKILL.md
- Extract patterns for: models, migrations, queries, relationships
- Include real code examples from the codebase
- 400-500 lines

Agent 5 - Deployment Skill:
- Analyze: [Dockerfile, CI/CD, configs]
- Create: .cursor/skills/[project]-deployment/SKILL.md
- Extract patterns for: Docker, CI/CD, env vars, deployment process
- Include real code examples from the codebase
- 400-500 lines

Agent 6 - Conventions Skill:
- Analyze: [entire codebase structure]
- Create: .cursor/skills/[project]-conventions/SKILL.md
- Extract patterns for: naming, formatting, comments, commits, file organization
- Include real code examples from the codebase
- 400-500 lines

Each skill should use this template structure:
- Version 1.0.0
- Changelog section
- Overview
- Multiple pattern sections with code examples
- Anti-patterns section
- Quick reference checklist
- Common mistakes
- Examples from actual codebase

After skills are created:

Agent 7 - Create .cursorrules:
- Consolidate all skills into a 200-300 line quick reference
- Place at project root
- Include core principles and file-specific triggers

Agent 8 - Create CLAUDE.md:
- Consolidate all skills into 800-1000 line comprehensive guide
- Place at .cursor/skills/CLAUDE.md
- Include quick jump navigation and common scenarios
- Add pattern quick reference table

Report back when all 8 tasks are complete with:
- Total lines created
- Files created
- Summary of patterns captured
```

---

## Validation Checklist

After creation, verify:

- [ ] **Individual skills created** (.cursor/skills/[project]-*/SKILL.md)
- [ ] **Each skill has real code examples** (not generic)
- [ ] **Anti-patterns documented** (what NOT to do)
- [ ] **.cursorrules created** (project root, 200-300 lines)
- [ ] **CLAUDE.md created** (.cursor/skills/, 800-1000 lines)
- [ ] **README updated** with "Using Skills" section
- [ ] **Test in Agent mode**: Open file, skills auto-apply
- [ ] **Test @ mention**: `@.cursor/skills/CLAUDE.md [question]`
- [ ] **Committed to git**

---

## Weekly Maintenance (15 minutes)

Every Friday:

```bash
# 1. Review quick notes
cat .cursor/skills/[project]-skill-improvement/logs/quick-notes.txt

# 2. Identify patterns
# - What worked well?
# - What was violated?
# - Any new patterns?

# 3. Update 1-2 skills if needed
# - Bump version (v1.0.0 → v1.0.1)
# - Add changelog entry
# - Update pattern

# 4. Clear quick notes for next week
echo "# Quick Notes - $(date +%Y-%m-%d)" > .cursor/skills/[project]-skill-improvement/logs/quick-notes.txt
```

---

## ROI Calculation (Monthly)

```
ROI = (Bugs Prevented × Avg Fix Time) / Time Invested

Example:
- Bugs prevented by skills: 5/month
- Avg fix time per bug: 2 hours
- Time invested: 1 hour/week = 4 hours/month

ROI = (5 × 2) / 4 = 2.5x return
```

---

## Common Mistakes

### 1. Too Generic
❌ "Follow best practices"  
✅ "Use authenticatedFetch(url, {method, body, headers}) for all POST/PUT/DELETE"

### 2. No Real Examples
❌ Describing patterns in prose only  
✅ Copy actual code from the project showing the pattern

### 3. No Maintenance
❌ Create once, never update  
✅ Weekly quick notes → monthly skill updates

---

## Next Steps

1. **Right now**: Use parallel agent prompt above (15 minutes)
2. **Today**: Create quick notes file, add first observation
3. **This week**: Tag skill violations in code reviews
4. **This Friday**: First 15-minute review
5. **Next month**: Calculate ROI

---

## Need More Detail?

See comprehensive guide: `CREATE-SKILLS-FOR-ANY-PROJECT.md` (1,241 lines)

**Reference implementation**: Adajoon project at `.cursor/skills/`

---

**Quick Start Version**: 1.0.0  
**Time to Complete**: 30-60 minutes  
**Ongoing Maintenance**: 15 min/week
