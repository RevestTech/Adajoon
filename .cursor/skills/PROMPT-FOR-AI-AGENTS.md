# Copy-Paste Prompt for AI Agents to Create Skills

**Use this prompt with any AI agent (Claude, GPT, etc.) to create a skill system for any project.**

---

## Quick Start Prompt (Copy Everything Below)

```
I want you to create a comprehensive skill system for my project, similar to the Adajoon implementation.

IMPORTANT: Extract patterns from MY actual codebase, not generic best practices!

=== PROJECT INFORMATION ===

Project Name: [YOUR_PROJECT_NAME]
Project Type: [Private / Company / Open Source / Client]
Tech Stack:
- Backend: [e.g., FastAPI, Django, Express, etc.]
- Frontend: [e.g., React, Vue, Angular, etc.]
- Database: [e.g., PostgreSQL, MongoDB, etc.]
- Deployment: [e.g., Railway, AWS, GCP, etc.]

Main Directories: [e.g., backend/, frontend/, src/]

Existing Rules/Guides: [List any company style guides, compliance requirements, or team conventions]

=== YOUR TASK ===

Phase 1: Analyze the Codebase (10-15 minutes)

1. Understand project context:
   - Is this a company project? (needs company style guide skill FIRST)
   - Are there existing style guides or compliance requirements?
   - What makes THIS project unique?

2. Read actual files, don't assume patterns:
   - Backend: Find and read main API files, auth files, config files
   - Frontend: Find and read main components, API clients, auth flows
   - Database: Find and read models, migrations
   - Deployment: Find and read Dockerfile, CI/CD configs
   - Look for existing .cursorrules, CONTRIBUTING.md, style guides

3. Extract ACTUAL patterns (not what "should be"):
   - How is auth ACTUALLY implemented?
   - What patterns does the code ACTUALLY use?
   - Why were these decisions made?
   - What are the exceptions to the rules?

Phase 2: Create Skills (Use Parallel Agents if Possible)

For Company Projects, create skills in this order:
1. Company style guide skill (FIRST - foundation)
2. Backend skill (reference company skill)
3. Frontend skill (reference company skill)
4. Security + compliance skill
5. Database skill
6. Deployment skill
7. Conventions skill
8. Skill improvement meta-skill

For Private Projects, create:
1. Backend skill
2. Frontend skill
3. Security skill
4. Database skill
5. Deployment skill
6. Conventions skill
7. Skill improvement meta-skill

Each skill should be 300-600 lines with:
- Version 1.0.0
- Real code examples from THIS codebase
- Explanation of WHY patterns exist
- Anti-patterns to avoid
- Quick reference checklist
- Common mistakes section

Phase 3: Create Unified Access System

Create these files:
1. `.cursorrules` (project root, 200-400 lines)
   - Concise summary for Cursor's built-in system
   - File-specific triggers

2. `.cursor/skills/CLAUDE.md` (800-1200 lines)
   - Comprehensive searchable reference
   - For @ mentions and copy/paste

3. Update README.md with "Using Skills" section

Phase 4: Set Up Continuous Improvement

Create directory structure:
```
.cursor/skills/[project]-skill-improvement/
├── SKILL.md (Karpathy-style methodology)
├── logs/quick-notes.txt
├── learnings/ (for incident documentation)
├── reviews/ (weekly templates)
└── audits/ (monthly templates)
```

=== CRITICAL RULES ===

❌ DO NOT create generic "best practices" skills
❌ DO NOT assume patterns - read actual code
❌ DO NOT copy examples from other projects
❌ DO NOT create skills longer than 600 lines

✅ DO extract patterns from THIS codebase
✅ DO explain WHY patterns exist
✅ DO include real code examples from project
✅ DO document exceptions and edge cases
✅ DO include project-specific context

=== EXAMPLES OF GOOD vs BAD ===

❌ BAD (Generic):
"Use JWT for authentication and follow best practices."

✅ GOOD (Project-Specific):
"Use cookie-based JWT stored in 'auth_token' cookie with httponly, 
secure, SameSite=Lax. Backend reads via Cookie() dependency, falls 
back to Authorization header. Why: XSS protection + OAuth compatibility. 
Tradeoff: Requires CSRF protection (we use csrf_token cookie)."

=== TEMPLATE STRUCTURE ===

Each skill should follow this structure:

```markdown
# [Project] [Area] Patterns

**Version**: 1.0.0
**Last Updated**: [Date]
**Triggers**: When working with [file patterns]

## Changelog
- v1.0.0: Initial version

## Overview
[What this skill covers and why it matters for THIS project]

## Pattern 1: [Name]

### When to Use
[Specific conditions in THIS project]

### Implementation
```[language]
// ACTUAL code from THIS codebase
```

### Why This Pattern
[Explain the decision and tradeoffs]

### Anti-Patterns
❌ Don't: [what NOT to do]
✅ Do: [correct approach]

[Repeat for all major patterns]

## Quick Reference Checklist
- [ ] Item 1
- [ ] Item 2

## Common Mistakes
1. Mistake: [description]
   Fix: [solution]

## Examples from Codebase
[Real code showing patterns in action]
```

=== REFERENCE IMPLEMENTATION ===

For complete examples, see Adajoon project:
- https://github.com/RevestTech/Adajoon/tree/main/.cursor/skills

Detailed guides:
- Full guide: CREATE-SKILLS-FOR-ANY-PROJECT.md (1,241 lines)
- Quick start: QUICK-START-SKILL-CREATION.md (condensed)

=== DELIVERABLES ===

When complete, provide:
1. List of all skills created with line counts
2. Summary of patterns captured
3. .cursorrules summary
4. CLAUDE.md table of contents
5. Instructions for using the skills

=== START NOW ===

Begin by analyzing the project context and reading actual files.
Report back with:
1. Project type analysis
2. Existing rules found
3. Proposed skill list (prioritized)
4. Key patterns identified

Then proceed with parallel skill creation.
```

---

## How to Use This Prompt

### For AI Agents (Recommended)

1. **Copy the entire prompt above** (between the ``` marks)
2. **Fill in your project information**:
   - Project name
   - Project type (Private/Company/Open Source)
   - Tech stack
   - Main directories
   - Any existing style guides
3. **Paste into Claude, GPT, or Cursor Agent**
4. **Let the agent analyze and create skills**

### For Cursor Agent Mode

```bash
# In Cursor, open a chat and paste:
@[workspace] Create a skill system using this prompt:
[paste filled-in prompt]
```

### For Direct Claude Conversations

1. Open Claude.ai
2. Paste the filled-in prompt
3. Provide file paths when Claude asks
4. Review and iterate on generated skills

---

## Example: Filled-In Prompt

```
I want you to create a comprehensive skill system for my project, similar to the Adajoon implementation.

IMPORTANT: Extract patterns from MY actual codebase, not generic best practices!

=== PROJECT INFORMATION ===

Project Name: MyApp
Project Type: Company (Future Capital)
Tech Stack:
- Backend: Django REST Framework, Python 3.11
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Database: PostgreSQL 15
- Deployment: AWS ECS, GitHub Actions

Main Directories: backend/, frontend/, infrastructure/

Existing Rules/Guides: 
- Future Capital Style Guide (terminology, tone, compliance)
- SOC2 compliance requirements
- Team convention: Conventional Commits

=== YOUR TASK ===
[rest of prompt...]
```

---

## What You'll Get

After running this prompt, the AI agent will create:

**Files:**
```
.cursorrules                                    # 200-400 lines
.cursor/skills/
├── README.md                                   # Overview
├── CLAUDE.md                                   # 800-1200 lines
├── [project]-backend/SKILL.md                  # 400-600 lines
├── [project]-frontend/SKILL.md                 # 400-600 lines
├── [project]-security/SKILL.md                 # 400-600 lines
├── [project]-database/SKILL.md                 # 400-600 lines
├── [project]-deployment/SKILL.md               # 400-600 lines
├── [project]-conventions/SKILL.md              # 400-600 lines
└── [project]-skill-improvement/
    ├── SKILL.md
    ├── logs/quick-notes.txt
    ├── learnings/
    ├── reviews/
    └── audits/
```

**Total:** ~4,500-5,000 lines of project-specific guidelines

---

## Time Estimate

- **Sequential creation**: 2-3 hours
- **Parallel agents**: 30-60 minutes
- **Ongoing maintenance**: 15 min/week

---

## Validation Checklist

After skills are created:

- [ ] Skills extract patterns from YOUR actual code (not generic)
- [ ] Each skill includes real code examples from project
- [ ] Company style guide skill exists (if company project)
- [ ] Anti-patterns documented (what NOT to do)
- [ ] .cursorrules created and concise
- [ ] CLAUDE.md created and comprehensive
- [ ] README updated with "Using Skills" section
- [ ] Test in Cursor Agent mode (skills auto-apply)
- [ ] Test @ mention: `@.cursor/skills/CLAUDE.md [question]`

---

## Quick Reference

| Project Type | First Skill | Focus |
|--------------|-------------|-------|
| **Company** | Company style guide | Standards + technical + compliance |
| **Private** | Backend patterns | Technical architecture |
| **Open Source** | Contribution guide | Contributors + API stability |

---

## Support

If the AI agent asks for clarification:
- **"What patterns should I use?"** → "Read the actual code, extract what you see"
- **"Should I add X pattern?"** → "Is X actually used in the codebase?"
- **"How should I structure Y?"** → "Look at how Y is currently implemented"

**Remember**: Skills document YOUR project, not ideal best practices!

---

**Last Updated**: 2026-04-04  
**Based on**: Adajoon v2.4.0 skill system
