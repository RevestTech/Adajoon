# How to Create Comprehensive Skills for Any Project

**AI Agent Instructions:** Follow this guide to create a complete skill system similar to the Adajoon project. This works for any codebase and creates skills that work in Cursor Agent, Cursor Composer/Chat, and direct Claude conversations.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Analyze the Codebase](#phase-1-analyze-the-codebase)
4. [Phase 2: Create Individual Skills](#phase-2-create-individual-skills)
5. [Phase 3: Create Unified Access System](#phase-3-create-unified-access-system)
6. [Phase 4: Add Continuous Improvement](#phase-4-add-continuous-improvement)
7. [Phase 5: Document and Deploy](#phase-5-document-and-deploy)
8. [Templates and Examples](#templates-and-examples)
9. [Success Criteria](#success-criteria)

---

## Overview

### What is a Skill System?

A comprehensive skill system provides AI assistants with **project-specific** coding patterns, conventions, and best practices. It ensures consistency across the codebase and prevents common mistakes.

### ⚠️ CRITICAL: Skills Must Reflect YOUR Project

**DO NOT create generic "best practices" skills!**

Each project has unique:
- **Context**: Private project vs company project vs open source
- **Patterns**: Actual coding patterns used in THIS codebase
- **Rules**: Company style guides, team conventions, regulatory requirements
- **Technology**: Specific frameworks, libraries, versions
- **Architecture**: Unique design decisions and tradeoffs

**Examples:**
- ❌ Generic: "Use RESTful API design"
- ✅ Project-specific: "All endpoints use `/api/v1/` prefix. Use cookie-based JWT (not Authorization header). CSRF tokens required on mutations."

- ❌ Generic: "Follow React best practices"  
- ✅ Project-specific: "Components in `src/components/`, hooks in `src/hooks/`. Use authenticatedFetch() wrapper for all API calls. OAuth via Google/Apple using window.postMessage pattern."

- ❌ Generic: "Use company branding"
- ✅ Company-specific: "Follow Future Capital Style Guide. Use 'plan sponsors' not 'employers'. Products: IMA, Core, Select, Construct (capitalize). No superlatives."

**Analysis Process:**
1. **Read the codebase** - Look at ACTUAL files, not assumptions
2. **Extract patterns** - What does THIS project actually do?
3. **Document context** - Why were these decisions made?
4. **Capture exceptions** - When do the rules NOT apply?

### Three-Tier Architecture

```
Single Source of Truth (.cursor/skills/<skill-name>/SKILL.md)
         ↓
    ┌────────┬────────┬────────┐
    ↓        ↓        ↓        ↓
.cursorrules CLAUDE.md Agent  README
(concise)   (detailed) (auto) (docs)
```

### Benefits

- ✅ **Consistency**: All code follows same patterns
- ✅ **Quality**: Enforces best practices automatically
- ✅ **Speed**: Quick reference instead of searching docs
- ✅ **Learning**: Captures institutional knowledge
- ✅ **Evolution**: Continuous improvement process

---

## Prerequisites

Before starting, ensure you have:

1. **Codebase Access**: Read access to all project files
2. **Git Repository**: Version control for tracking changes
3. **Project Understanding**: Know the tech stack and architecture
4. **Time**: Allow 2-4 hours for initial skill creation

---

## Phase 1: Analyze the Codebase

### Step 1.1: Understand Project Context

**BEFORE analyzing technical areas, understand the project context:**

#### Project Type

**Private Project** (e.g., Adajoon):
- Focus: Technical patterns, architecture decisions
- Scope: Team/individual preferences
- Examples: Authentication approach, caching strategy, deployment setup

**Company Project** (e.g., Future Capital):
- Focus: Technical patterns + company standards + compliance
- Scope: Company style guide, regulatory requirements, brand guidelines
- Examples: FC style guide skill, financial compliance patterns, approved terminology

**Open Source Project**:
- Focus: Contributor guidelines, API stability, documentation
- Scope: Broad community, clear documentation, versioning
- Examples: Contribution process, breaking change policy, public API patterns

**Client Project**:
- Focus: Client requirements, handoff documentation, maintainability
- Scope: Client preferences, contractual requirements
- Examples: Client-approved patterns, specific framework choices, documentation standards

#### Existing Rules and Guidelines

**Check for existing documentation:**
```bash
# Look for existing style guides
find . -name "*STYLE*" -o -name "*GUIDE*" -o -name "*CONVENTION*" -o -name "CONTRIBUTING.md"

# Check for company/team standards
find . -name ".cursorrules" -o -name ".cursor/rules/" -o -name "docs/standards/"

# Look for linter configs (reflect actual preferences)
find . -name ".eslintrc*" -o -name "pyproject.toml" -o -name ".prettierrc*"
```

**Examples of existing rules to integrate:**
- Company style guide (e.g., Future Capital style guide skill)
- Regulatory compliance (HIPAA, SOC2, GDPR, financial regulations)
- Brand guidelines (terminology, tone, visual standards)
- Team conventions (code review process, commit format)
- Client requirements (specific patterns, technologies)

#### Integration Strategy

If existing rules/guides exist:

1. **Create a company/brand skill FIRST**
   - Example: `fc-style-guide/SKILL.md` for Future Capital projects
   - Example: `company-compliance/SKILL.md` for regulated industries
   - This becomes the foundation for other skills

2. **Reference company skill from technical skills**
   - Backend skill: "Follow company API naming from company-standards skill"
   - Frontend skill: "Use approved terminology from company-style-guide skill"

3. **Don't duplicate - cross-reference**
   - ❌ "Use 'plan sponsors' terminology" in 5 different skills
   - ✅ "See fc-style-guide skill for terminology" in technical skills

### Step 1.2: Identify Technology Areas

**NOW analyze technical areas specific to THIS project:**

**Look at actual directory structure:**
```bash
# What does THIS project actually have?
ls -la
find . -type d -maxdepth 2 | head -20
```

**Examples based on real project structure:**

**Adajoon (Streaming Platform - Private):**
```
1. Backend API patterns (FastAPI, cookie-based JWT)
2. Frontend patterns (React, OAuth, authenticatedFetch)
3. Database patterns (SQLAlchemy async, Alembic)
4. Security patterns (COOP headers for OAuth, CSRF tokens)
5. Deployment patterns (Railway dual-service, backend-as-proxy)
6. Code conventions (Python type hints, no obvious comments)
```

**Future Capital (Financial - Company):**
```
1. FC style guide (terminology, tone, compliance language)
2. Backend API patterns (specific to FC's architecture)
3. Frontend patterns (FC brand components, approved libraries)
4. Financial compliance (data handling, audit trails)
5. Deployment patterns (FC's infrastructure)
6. Code conventions (FC's code review standards)
```

**E-commerce Platform:**
```
1. Backend API patterns (product catalog, checkout flow)
2. Frontend patterns (cart state, payment integration)
3. Database patterns (inventory, order management)
4. Security patterns (PCI compliance, customer data)
5. Payment integration patterns (Stripe, PayPal)
6. Code conventions (team standards)
```

**The technology areas are unique to EACH project based on:**
- What the project actually does
- What technologies it actually uses
- What patterns it actually follows
- What rules/regulations apply to it

### Step 1.3: Analyze Each Area (Extract Real Patterns)

**For each technical area, examine ACTUAL code in THIS project:**

#### Analysis Process

**1. Read Real Files (Don't Assume)**

```bash
# Find actual backend files
find backend/ api/ src/ -name "*.py" -o -name "*.js" -o -name "*.ts" 2>/dev/null | head -20

# Find actual frontend files  
find frontend/ client/ src/components/ -name "*.jsx" -o -name "*.tsx" -o -name "*.vue" 2>/dev/null | head -20

# Find actual config files
find . -name "Dockerfile" -o -name "docker-compose.yml" -o -name ".env.example" -o -name "config.*"
```

**2. Extract Patterns from Real Code**

**Example: Authentication Pattern Analysis**

Read: `backend/app/routers/auth.py` or equivalent

**Look for:**
- How is auth actually implemented? (JWT? Session? OAuth?)
- Where is the token stored? (Cookie? Header? LocalStorage?)
- What dependencies are used? (FastAPI Cookie? Authorization header?)
- What are the actual function signatures?

**Document what you SEE, not what you think should be:**
```markdown
✅ GOOD - Actual Pattern:
"Authentication uses cookie-based JWT. Token stored in 'auth_token' cookie 
with httponly, secure, SameSite=Lax attributes. Backend reads token using 
FastAPI Cookie dependency: `token: str = Cookie(None, alias="auth_token")`. 
Falls back to Authorization header for API clients."

❌ BAD - Generic:
"Use JWT for authentication and follow best practices."
```

**3. Document Actual Decisions and Tradeoffs**

**Example: Why this pattern?**
```markdown
## Cookie-Based JWT (Not Authorization Header)

**Pattern**: JWT stored in httpOnly cookie, not Authorization header

**Why**: 
- XSS protection (httpOnly prevents JavaScript access)
- OAuth flows work better with cookies (Google/Apple redirect patterns)
- Domain cookies allow backend/worker services to share auth

**Tradeoff**: 
- CSRF protection required (we use csrf_token cookie + X-CSRF-Token header)
- More complex than Bearer token
- Doesn't work with some API testing tools (use fallback header)

**When NOT to use**:
- Public API for third-party clients (they need Bearer tokens)
- Non-browser clients (mobile apps, CLI tools)
```

**4. Patterns to Extract (Project-Specific)**

**Backend:**
- ✅ Actual routing structure (prefixes, versioning)
- ✅ Real authentication/authorization flow
- ✅ Actual error handling (HTTP exceptions, logging)
- ✅ Database connection/session management as implemented
- ✅ Caching strategy actually used
- ✅ Real middleware stack and order

**Frontend:**
- ✅ Actual component structure and file organization
- ✅ State management as implemented (Context, Redux, Zustand, etc.)
- ✅ Real API call patterns (fetch wrapper, axios, etc.)
- ✅ Authentication flow actually used
- ✅ Routing implementation
- ✅ Form handling patterns

**Database:**
- ✅ Actual ORM/query patterns used
- ✅ Migration tool actually used (Alembic, Prisma, etc.)
- ✅ Real model relationships and constraints
- ✅ Actual query optimization approaches

**Company/Brand (if applicable):**
- ✅ Actual terminology used (read docs, UI text)
- ✅ Real tone and voice in existing content
- ✅ Actual compliance requirements
- ✅ Approved vendors/technologies
- ✅ Brand color codes, fonts, styling

**Security:**
- ✅ Actual security headers configured
- ✅ Real input validation approach
- ✅ CSRF/XSS protection as implemented
- ✅ Rate limiting strategy
- ✅ Secrets management approach

**5. Capture Exceptions and Edge Cases**

```markdown
## API Versioning Pattern

**Standard**: All endpoints use `/api/v1/` prefix

**Exceptions**:
- Health checks: `/health` (no version, must be stable)
- Metrics: `/metrics` (Prometheus standard, no version)
- OAuth callbacks: `/api/auth/{provider}/callback` (no version, external dependencies)

**Why exceptions exist**: [reason for each]
```

### Step 1.4: Create Skill List (Project-Specific)

Based on your ACTUAL project analysis, create a prioritized list:

**For Company Projects (e.g., Future Capital):**

**Priority 1 (Company Standards):**
1. **Company style guide skill** (terminology, tone, compliance)
   - MUST exist before technical skills
   - Foundation for all other skills

**Priority 2 (Core Technical Patterns):**
2. Backend/API skill (reference company skill for naming)
3. Frontend skill (reference company skill for content)
4. Security skill (include company compliance requirements)

**Priority 3 (Infrastructure):**
5. Database skill (include audit trail requirements if needed)
6. Deployment skill (company infrastructure)

**Priority 4 (Quality):**
7. Code conventions skill (company code review standards)
8. Continuous improvement meta-skill

**For Private Projects (e.g., Adajoon):**

**Priority 1 (Core Technical Patterns):**
1. Backend/API skill
2. Frontend skill
3. Security skill

**Priority 2 (Infrastructure):**
4. Database skill
5. Deployment skill

**Priority 3 (Quality):**
6. Code conventions skill
7. Continuous improvement meta-skill

**For Open Source Projects:**

**Priority 1 (Contributor Experience):**
1. Contribution guidelines skill
2. Code conventions skill
3. API stability skill

**Priority 2 (Core Technical):**
4. Backend/API skill
5. Frontend skill
6. Security skill

**Priority 3 (Infrastructure):**
7. Testing skill (critical for open source)
8. Documentation skill
9. Release process skill

**Adjust based on your project's actual needs!**

---

## Phase 2: Create Individual Skills

### Step 2.1: Set Up Directory Structure

Create the skills directory:

```bash
mkdir -p .cursor/skills
```

### Step 2.2: Create Each Skill File

For each skill area, create a comprehensive SKILL.md file.

**Directory naming convention:**
```
.cursor/skills/<project-name>-<area>/SKILL.md
```

**Example:**
```
.cursor/skills/myapp-backend/SKILL.md
.cursor/skills/myapp-frontend/SKILL.md
.cursor/skills/myapp-security/SKILL.md
```

### Step 2.3: Skill File Template

Use this template for each SKILL.md file:

```markdown
# [Project Name] [Area] Patterns

**Version**: 1.0.0  
**Last Updated**: [Date]  
**Skill Type**: [Backend/Frontend/Security/etc.]  
**Auto-triggers**: When working with [file patterns]

## Changelog
- v1.0.0 ([Date]): Initial version

---

## Overview

Brief description of what this skill covers and why it matters.

---

## [Pattern Category 1]

### When to Use
Describe when this pattern applies.

### Pattern
```[language]
// Code example showing the pattern
```

### Key Points
- Point 1
- Point 2
- Point 3

### Anti-Patterns (What NOT to Do)
❌ Bad example
✅ Good example

---

## [Pattern Category 2]

[Repeat structure for each category]

---

## Quick Reference Checklist

Use this checklist when [creating/reviewing] [type of code]:

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

---

## Common Mistakes

1. **Mistake**: Description
   - **Why it's wrong**: Explanation
   - **Fix**: Correct approach

---

## Related Skills

- [link to related skill]
- [link to another related skill]

---

## Examples from Codebase

### Example 1: [Description]
```[language]
// Real code from the project
```

**Why this works**: Explanation

---

## Version History

- v1.0.0 ([Date]): Initial patterns extracted from codebase
```

### Step 2.4: Content Guidelines

**Each skill should be:**

1. **Comprehensive** (300-600 lines)
   - Cover all major patterns in that area
   - Include both dos and don'ts
   - Provide code examples

2. **Practical**
   - Use real examples from the codebase
   - Include checklists for common tasks
   - Show anti-patterns to avoid

3. **Searchable**
   - Use clear headings (## and ###)
   - Include keyword-rich section names
   - Add cross-references to related skills

4. **Actionable**
   - Specific rules, not vague advice
   - Include "when to use" guidance
   - Provide quick reference checklists

### Step 2.5: Use Parallel Agent Swarm (Optional but Recommended)

To create skills faster, use parallel agents:

**Prompt for launching swarm:**
```
Launch 6 agents in parallel to create skills for my project:

Agent 1: Create [project]-backend skill by analyzing:
- [list key backend files]
Extract patterns for: routing, authentication, error handling, etc.

Agent 2: Create [project]-frontend skill by analyzing:
- [list key frontend files]
Extract patterns for: components, state, API calls, etc.

Agent 3: Create [project]-security skill by analyzing:
- [list security-related files]
Extract patterns for: auth, validation, headers, etc.

Agent 4: Create [project]-database skill by analyzing:
- [list database/model files]
Extract patterns for: models, migrations, queries, etc.

Agent 5: Create [project]-deployment skill by analyzing:
- [list deployment files]
Extract patterns for: Docker, CI/CD, env vars, etc.

Agent 6: Create [project]-conventions skill by analyzing:
- [entire codebase structure]
Extract patterns for: naming, formatting, comments, commits, etc.

Each skill should be 300-600 lines, include examples from the codebase,
and follow the template at [link or paste template].
```

---

## Phase 3: Create Unified Access System

After creating individual skills, make them accessible across all contexts.

### Step 3.1: Create .cursorrules

Create a concise summary at the project root:

**File: `.cursorrules`**

**Target length**: 200-400 lines  
**Purpose**: Quick reference for Cursor's built-in system

**Structure:**
```markdown
# [Project Name] Project Rules

Quick-reference rules for Cursor's built-in system.
For details, see .cursor/skills/ or @.cursor/skills/CLAUDE.md

## Project Context
- Stack: [tech stack]
- Architecture: [brief description]

## Core Principles
1. Principle 1
2. Principle 2
3. Principle 3

---

## [Area 1] Patterns

### When: [file patterns]

**Key Rules:**
- Rule 1
- Rule 2
- Rule 3

**Quick Checklist:**
- [ ] Item 1
- [ ] Item 2

---

## [Area 2] Patterns

[Repeat for each skill area]

---

## Common Patterns Across All Code

### File Organization
- Pattern 1
- Pattern 2

### Error Handling
- Pattern 1
- Pattern 2

### Testing
- Pattern 1
- Pattern 2

---

## Quick Reference

| Task | Skill to Reference | Key Pattern |
|------|-------------------|-------------|
| API endpoint | [skill] | [pattern] |
| Component | [skill] | [pattern] |
```

### Step 3.2: Create CLAUDE.md

Create a comprehensive searchable reference:

**File: `.cursor/skills/CLAUDE.md`**

**Target length**: 800-1200 lines  
**Purpose**: @ mention reference for Composer/Chat and copy/paste for direct Claude

**Structure:**
```markdown
# [Project Name] Skills Reference for Claude Conversations

Comprehensive guide for all [project] coding patterns.
Use with `@.cursor/skills/CLAUDE.md` or copy/paste sections.

**Quick Jump**:
- [Backend](#backend)
- [Frontend](#frontend)
- [Security](#security)
- [Database](#database)
- [Deployment](#deployment)
- [Conventions](#conventions)
- [Common Scenarios](#common-scenarios)

---

## Project Overview

### Stack
[Description of tech stack]

### Architecture
```
[ASCII diagram of architecture]
```

### Key Technologies
- Backend: [tech + version]
- Frontend: [tech + version]
- Database: [tech + version]
- Deployment: [platform]

---

## Backend

[Consolidated patterns from backend skill]

### Router Structure
[Pattern]

### Authentication
[Pattern]

### Error Handling
[Pattern]

---

## Frontend

[Consolidated patterns from frontend skill]

---

## Security

[Consolidated patterns from security skill]

---

## Database

[Consolidated patterns from database skill]

---

## Deployment

[Consolidated patterns from deployment skill]

---

## Conventions

[Consolidated patterns from conventions skill]

---

## Common Scenarios

### How do I create a new API endpoint?
1. Step 1
2. Step 2
3. Reference: [skill section]

### How do I add authentication to a component?
1. Step 1
2. Step 2
3. Reference: [skill section]

[Add 10-15 common scenarios]

---

## Pattern Quick Reference

| I need to... | Look here | Key pattern |
|--------------|-----------|-------------|
| Create endpoint | [section] | [pattern] |
| Add auth | [section] | [pattern] |

---

## Skill File References

For deep dives, see:
- [Backend](./<project>-backend/SKILL.md)
- [Frontend](./<project>-frontend/SKILL.md)
- [Security](./<project>-security/SKILL.md)
- [Database](./<project>-database/SKILL.md)
- [Deployment](./<project>-deployment/SKILL.md)
- [Conventions](./<project>-conventions/SKILL.md)
```

### Step 3.3: Update README.md

Add a "Using Skills" section to the main README:

```markdown
## Using Skills

This project includes comprehensive coding skills to ensure consistency.
Skills work across different AI assistant contexts.

### 🤖 Cursor Agent Mode (Automatic)

Skills automatically load from `.cursor/skills/` based on context.
Just code normally - patterns enforce automatically! ✨

### 💬 Cursor Composer/Chat Mode

Use @ mentions to reference skills:

```bash
# Press Cmd+I (Composer) or Cmd+L (Chat)
@.cursor/skills/CLAUDE.md how do I create an API endpoint?
@.cursor/skills/CLAUDE.md what are the authentication patterns?
```

The `.cursorrules` file provides quick reference automatically.

### 🤖 Direct Claude Conversations

1. Open `.cursor/skills/CLAUDE.md`
2. Search for your topic (Cmd/Ctrl+F)
3. Copy relevant section
4. Paste into conversation

### 📚 Available Skills

| Skill | Coverage |
|-------|----------|
| [project]-backend | [description] |
| [project]-frontend | [description] |
| [project]-security | [description] |
| [project]-database | [description] |
| [project]-deployment | [description] |
| [project]-conventions | [description] |

See `.cursor/skills/README.md` for complete documentation.
```

---

## Phase 4: Add Continuous Improvement

Create a meta-skill for evolving the skill system over time.

### Step 4.1: Create Skill Improvement Skill

**File: `.cursor/skills/<project>-skill-improvement/SKILL.md`**

Use the Karpathy-style learning methodology:

```markdown
# [Project Name] Skill Improvement Process

**Version**: 1.0.0  
**Based on**: Andrej Karpathy's iterative learning methodology

## Overview

This skill describes how to continuously improve all project skills
based on real-world feedback, incidents, and learnings.

---

## 1. Iterative Refinement

### Track What Works vs What Doesn't

**Daily Observations:**
Keep a quick notes file: `.cursor/skills/<project>-skill-improvement/logs/quick-notes.txt`

```txt
YYYY-MM-DD: ✅ Pattern worked well: [description]
YYYY-MM-DD: ⚠️ Pattern violated: [description]
YYYY-MM-DD: 💡 New pattern emerged: [description]
```

### Log Deviations

When skills are violated, document in:
`.cursor/skills/<project>-skill-improvement/logs/deviations.md`

**Format:**
```markdown
## [Date] - [Skill] - [Pattern Violated]

**What happened**: [description]
**Why it happened**: [root cause]
**Impact**: [severity: low/medium/high]
**Action**: [update skill / clarify pattern / acceptable exception]
```

---

## 2. Learning by Doing

### Document Incidents

When bugs occur or incidents happen, document the learning:

**File**: `.cursor/skills/<project>-skill-improvement/learnings/YYYY-MM-DD-short-description.md`

**Template:**
```markdown
# Learning: [Short Title]

**Date**: YYYY-MM-DD  
**Severity**: [Low/Medium/High/Critical]  
**Time to Resolution**: [minutes/hours]

## What Happened
[Description of the incident]

## Why It Happened
[Root cause analysis]

## The Fix
[What was done to resolve]

## Prevention Strategy
[How to prevent recurrence]

### Skill Updates Required
- [ ] Update [skill-name] v[X.Y.Z] → v[X.Y.Z+1]
- [ ] Add section on [topic]
- [ ] Update checklist

## Metrics
- Detection time: [time]
- Resolution time: [time]
- Recurrence risk: [low/medium/high]

## Related Skills
- [skill link]
```

---

## 3. Self-Review Process

### Before Committing (Daily)
- [ ] Does code follow all applicable skill patterns?
- [ ] Are there any skill violations?
- [ ] Should any new patterns be documented?

### Weekly Review (Fridays, 15 minutes)

**Template**: `.cursor/skills/<project>-skill-improvement/reviews/weekly-template.md`

```markdown
# Weekly Skill Review - [Date]

## Patterns That Worked Well
- Pattern 1
- Pattern 2

## Patterns Violated (from quick notes)
- Violation 1 → [update skill / clarify / acceptable]
- Violation 2 → [action]

## New Patterns Observed
- Pattern 1 → [add to skill]
- Pattern 2 → [document next week]

## Skill Updates This Week
- [skill-name] v[X.Y.Z] → v[X.Y.Z+1]: [change]

## Action Items
- [ ] Item 1
- [ ] Item 2
```

### Monthly Audit (30 minutes)

**Template**: `.cursor/skills/<project>-skill-improvement/audits/monthly-template.md`

```markdown
# Monthly Skill Audit - [Month Year]

## Metrics

### Leading Indicators
- Skill violations: [count] ([trend: ↓↑→])
- Time to update skills: [avg time]
- Team engagement: [subjective assessment]

### Lagging Indicators
- Bugs prevented by skills: [estimate]
- Bug recurrence rate: [%]
- Code review time saved: [estimate]

### ROI Calculation
```
ROI = (Bugs Prevented × Avg Fix Time) / Time Invested in Skills
    = ([X] bugs × [Y] hours) / [Z] hours
    = [ROI]x return
```

## Most Violated Skills
1. [skill-name]: [count] violations
2. [skill-name]: [count] violations

## Most Effective Skills
1. [skill-name]: [bugs prevented]
2. [skill-name]: [bugs prevented]

## Gaps Identified
- Missing pattern: [description]
- Unclear pattern: [description]

## Skill Updates Planned
- [ ] [skill-name]: [planned change]
- [ ] [skill-name]: [planned change]

## Meta-Learning
What did we learn about the skill system itself?
- Learning 1
- Learning 2
```

---

## 4. Feedback Loops

### Code Review Comments → Skill Updates

When reviewers repeatedly mention the same issue:

**Process:**
1. Tag comment with `[SKILL:skill-name]`
2. After 3rd occurrence, update skill
3. Version bump and document in changelog

**Example:**
```markdown
# Code Review
[SKILL:backend] Missing input validation on user_id parameter.
See "Input Validation" section in backend skill.
```

### Bug Fixes → Pattern Documentation

**Process:**
1. Fix bug
2. Document in `learnings/`
3. Update relevant skill within 24 hours
4. Add to prevention checklist

### Performance Issues → Best Practices

When performance issues occur:
1. Document the issue and fix
2. Add performance pattern to relevant skill
3. Update "Anti-Patterns" section

---

## 5. Skill Evolution

### Versioning

Use semantic versioning for skills:

- **MAJOR** (v1 → v2): Breaking change in pattern
- **MINOR** (v1.0 → v1.1): New pattern added
- **PATCH** (v1.0.0 → v1.0.1): Clarification or fix

**Format:**
```markdown
# [Project] [Area] Patterns

**Version**: 1.2.3
**Last Updated**: YYYY-MM-DD

## Changelog
- v1.2.3 (YYYY-MM-DD): Fixed typo in example
- v1.2.0 (YYYY-MM-DD): Added async/await pattern
- v1.1.0 (YYYY-MM-DD): Added caching section
- v1.0.0 (YYYY-MM-DD): Initial version
```

### Deprecation Process

When deprecating a pattern:

1. **v[X.Y.0]**: Mark as deprecated, show alternative
```markdown
## Pattern X (DEPRECATED)

⚠️ **Deprecated in v1.5.0. Use Pattern Y instead.**

Old pattern still works but will be removed in v2.0.0.

**Migration guide**: [link]
```

2. **v[X+1.0.0]**: Remove deprecated pattern

---

## 6. Meta-Learning

### Questions to Ask Monthly

1. **Which skills are most violated?**
   - Needs clarification?
   - Too strict?
   - Not practical?

2. **Which skills prevent most bugs?**
   - High ROI
   - Should be emphasized
   - Should expand coverage

3. **Which skills need clarification?**
   - Repeated questions
   - Multiple interpretations
   - Add examples

4. **What's missing from skills?**
   - Gaps in coverage
   - New patterns emerging
   - Technology changes

### Success Metrics

**Skill System Health:**
- ✅ Weekly reviews completed: [%]
- ✅ Skills updated after incidents: [response time]
- ✅ Team engagement: [high/medium/low]

**Code Quality Impact:**
- ✅ Bug recurrence rate: [%]
- ✅ Code review iterations: [avg]
- ✅ Time to onboard new developers: [days]

**ROI:**
```
Monthly ROI = (Bugs Prevented × Fix Time) / Skill Maintenance Time
Example: (10 bugs × 2 hours) / (4 hours review + 2 hours updates)
       = 20 hours / 6 hours
       = 3.3x return on investment
```

---

## Getting Started Today

### Immediate (5 minutes)
1. Create `logs/quick-notes.txt`
2. Add first observation

### This Week
3. Tag skill violations in code reviews with `[SKILL:name]`
4. Document one learning if incident occurs

### This Friday (15 minutes)
5. Complete first weekly review using template

### Next Month (30 minutes)
6. Complete first monthly audit
7. Calculate ROI
8. Update skills based on learnings

---

## Templates Location

All templates are in:
```
.cursor/skills/<project>-skill-improvement/
├── logs/
│   ├── quick-notes.txt          (daily observations)
│   └── deviations.md            (skill violations)
├── learnings/
│   ├── README.md                (how to document learnings)
│   └── example-learning.md      (full example)
├── reviews/
│   └── weekly-template.md       (copy each Friday)
└── audits/
    └── monthly-template.md      (copy each month)
```

---

## Philosophy (Karpathy-Style)

1. **Learn by doing** - Skills improve through real implementation
2. **Track everything** - What works, what doesn't, why
3. **Iterate fast** - Small frequent updates beat large rewrites
4. **Build understanding** - Document the why, not just the what
5. **Test assumptions** - Validate patterns with real code

---

## Version History

- v1.0.0 ([Date]): Initial continuous improvement process
```

### Step 4.2: Create Directory Structure

```bash
mkdir -p .cursor/skills/<project>-skill-improvement/{logs,learnings,reviews,audits}

# Create templates
touch .cursor/skills/<project>-skill-improvement/logs/quick-notes.txt
touch .cursor/skills/<project>-skill-improvement/logs/deviations.md
touch .cursor/skills/<project>-skill-improvement/reviews/weekly-template.md
touch .cursor/skills/<project>-skill-improvement/audits/monthly-template.md
```

### Step 4.3: Create Example Learning

Create an example learning document to show the format:

**File**: `.cursor/skills/<project>-skill-improvement/learnings/example-learning.md`

---

## Phase 5: Document and Deploy

### Step 5.1: Create Skills README

**File**: `.cursor/skills/README.md`

```markdown
# [Project Name] Cursor Skills

Comprehensive coding skills for maintaining consistency and quality.

## Available Skills

### 1. **[project]-backend** ([lines] lines)
[Description]

**Triggers**: [patterns]  
**Covers**: [topics]

### 2. **[project]-frontend** ([lines] lines)
[Description]

**Triggers**: [patterns]  
**Covers**: [topics]

[Continue for all skills]

## Total Coverage

- **[N] specialized skills** covering all aspects of the codebase
- **~[X,XXX] lines** of comprehensive guidelines
- **3 access methods**: Agent (auto), Composer/Chat (@ mentions), Direct Claude (copy/paste)
- **Single source of truth** (individual SKILL.md files)

## Usage

See main README.md "Using Skills" section for detailed usage instructions.

## Maintenance

When updating project conventions:
1. Update the relevant skill file
2. Bump version number
3. Add changelog entry
4. Commit changes
5. Skills automatically reload

## Version

Created for [Project Name] v[X.Y.Z] ([Date])
```

### Step 5.2: Version Bump

Bump project version to reflect the addition of skills:

```bash
# Example for package.json
"version": "X.Y.Z" → "version": "X.Y+1.0"

# Example for Python
__version__ = "X.Y.Z" → __version__ = "X.Y+1.0"
```

### Step 5.3: Commit to Repository

```bash
git add .cursor/ .cursorrules README.md
git commit -m "feat: add comprehensive skill system

Created [N] specialized skills for [project] covering:
- [skill 1]: [description]
- [skill 2]: [description]
[...]

Unified access system:
- .cursorrules: Quick reference for Cursor
- CLAUDE.md: @ mention reference and copy/paste guide
- Individual SKILL.md files: Detailed patterns

Total: ~[X,XXX] lines of guidelines

Skills work in:
- Cursor Agent mode (automatic)
- Cursor Composer/Chat (@ mentions + .cursorrules)
- Direct Claude conversations (copy/paste)

Includes Karpathy-style continuous improvement process with:
- Weekly review process
- Monthly audit process
- Learning documentation system
- ROI tracking"

git push
```

---

## Templates and Examples

### Minimal Viable Skill

If you're short on time, start with this minimal template:

```markdown
# [Project] [Area] Patterns

**Version**: 1.0.0

## Core Rules

1. **Rule 1**: Description
   ```[language]
   // Example
   ```

2. **Rule 2**: Description
   ```[language]
   // Example
   ```

3. **Rule 3**: Description

## Anti-Patterns

❌ **Don't**: Bad example  
✅ **Do**: Good example

## Checklist

When [doing X]:
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## Examples from Codebase

```[language]
// Real example from project
```
```

Expand this over time as patterns emerge.

---

## Success Criteria

Your skill system is complete and effective when:

### Completeness Checklist

- [ ] **Skills cover all major technical areas** (backend, frontend, database, deployment, security, conventions)
- [ ] **Each skill is 300-600 lines** with comprehensive coverage
- [ ] **Examples from actual codebase** (not generic examples)
- [ ] **Anti-patterns documented** (what NOT to do)
- [ ] **Quick reference checklists** included
- [ ] **Version numbers and changelogs** present

### Accessibility Checklist

- [ ] **`.cursorrules` created** (200-400 lines) for Cursor built-in system
- [ ] **`CLAUDE.md` created** (800-1200 lines) for @ mentions and copy/paste
- [ ] **README updated** with "Using Skills" section
- [ ] **Individual SKILL.md files** organized in `.cursor/skills/`

### Improvement System Checklist

- [ ] **Skill improvement skill created** with Karpathy methodology
- [ ] **Directory structure created** (logs/, learnings/, reviews/, audits/)
- [ ] **Templates created** (weekly review, monthly audit)
- [ ] **Example learning documented**

### Documentation Checklist

- [ ] **Skills README created** with overview of all skills
- [ ] **Main README updated** with usage instructions
- [ ] **Version bumped** to reflect skill addition
- [ ] **Committed to git** with descriptive commit message

### Validation Checklist

- [ ] **Test in Cursor Agent**: Open file, verify skill applies automatically
- [ ] **Test in Composer**: Use `@.cursor/skills/CLAUDE.md` and verify response
- [ ] **Test quick notes**: Add observation to `logs/quick-notes.txt`
- [ ] **Test learning doc**: Document a simple learning
- [ ] **Team feedback**: Get feedback from at least one other developer

### Metrics for Success

After 1 week:
- ✅ At least 3 code reviews reference skills
- ✅ At least 1 quick note added
- ✅ First weekly review completed

After 1 month:
- ✅ At least 1 skill updated based on feedback
- ✅ First monthly audit completed
- ✅ Positive ROI calculated (time saved > time invested)

---

## Common Pitfalls to Avoid

### 1. Too Generic
❌ "Use best practices for authentication"  
✅ "Use cookie-based JWT with httponly, secure, SameSite=Lax attributes. Store in auth_token cookie. Read using get_current_user(token: str = Cookie(None)) dependency."

### 2. No Examples
❌ Just describing patterns in prose  
✅ Include 3-5 real code examples from the actual codebase

### 3. Too Long
❌ 1000+ line skill files that nobody reads  
✅ 300-600 lines with good organization and searchable headings

### 4. Isolated Skills
❌ Skills that don't reference each other  
✅ Cross-reference related skills, show how they work together

### 5. No Maintenance
❌ Create once and never update  
✅ Weekly quick notes, monthly audits, update after incidents

### 6. Wrong Level of Detail
❌ Either too high-level or too low-level  
✅ Balance principles with specific patterns and examples

### 7. No Continuous Improvement
❌ Static skills that never evolve  
✅ Karpathy-style learning system with regular reviews and updates

---

## FAQ

### Q: How long does it take to create skills?

**A:** Initial creation: 2-4 hours using parallel agents. Ongoing maintenance: 15 min/week + 30 min/month.

### Q: What if our codebase is inconsistent?

**A:** Document the *intended* patterns, not existing inconsistencies. Use skills to drive consistency improvements over time.

### Q: Should we include third-party library patterns?

**A:** Only if you have project-specific conventions for using them. Example: "Always use authenticatedFetch for mutations" (your utility) vs "Use fetch API" (generic).

### Q: How do we handle deprecated patterns?

**A:** Mark as deprecated in skill, provide migration path, remove in next major version. See deprecation process in skill-improvement skill.

### Q: What if team members disagree on patterns?

**A:** Document the decided pattern, note the tradeoff, and track if it works in practice. Update if evidence shows a better approach.

### Q: Do we need all 7 skill types?

**A:** Start with 3-4 core skills (backend, frontend, security, conventions). Add others as needed. The skill-improvement meta-skill is always valuable.

### Q: How do we measure ROI?

**A:** Track bugs prevented by skills (estimate based on code reviews). Calculate: `(Bugs Prevented × Avg Fix Time) / Time Invested in Skills`. Target: >2x return.

---

## Next Steps

After completing this guide:

1. **Week 1**: Create core skills (backend, frontend, security)
2. **Week 2**: Create infrastructure skills (database, deployment)
3. **Week 3**: Create quality skills (conventions, skill-improvement)
4. **Week 4**: Create unified system (.cursorrules, CLAUDE.md)
5. **Ongoing**: Weekly reviews, monthly audits, continuous improvement

---

## Reference Implementation

For a complete example, see the Adajoon project:
- `.cursor/skills/` directory
- `.cursorrules` file
- `.cursor/skills/CLAUDE.md`
- `.cursor/skills/adajoon-skill-improvement/` for Karpathy methodology

---

## Support

If you have questions while implementing this for your project:
1. Reference the Adajoon implementation as an example
2. Start small (3 skills) and expand
3. Focus on patterns that prevent real bugs, not theoretical best practices
4. Iterate based on team feedback

**Remember**: Skills are living documents. Start with good-enough skills and improve them based on real-world use. Perfect is the enemy of done.

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-04  
**Based on**: Adajoon project skill system
