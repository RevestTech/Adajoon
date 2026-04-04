# Unified Skill System

**Created**: 2026-04-04  
**Purpose**: Enable skills to work across Cursor Agent, Cursor Composer/Chat, and direct Claude conversations

---

## What Was Created

### 1. `.cursorrules` (Project Root)
**Location**: `/Users/khashsarrafi/Projects/Adajoon/.cursorrules`  
**Size**: 317 lines, 9.1KB  
**Purpose**: Concise summary for Cursor's built-in rules system

**Used by**:
- Cursor Agent mode (automatic)
- Cursor Composer mode (Cmd+I)
- Cursor Chat mode (Cmd+L)

**Content**:
- Quick-reference rules for all 7 skills
- File-specific triggers (e.g., `backend/routers/*.py` → Backend + Security)
- Essential patterns and checklists
- Critical anti-patterns
- Under 500 lines for fast loading

**Format**: Optimized for Cursor's rules parser
- Uses `###` headers for sections
- Bullet points for quick scanning
- Code blocks for examples
- Checklists for common tasks

---

### 2. `CLAUDE.md` (Skills Directory)
**Location**: `/Users/khashsarrafi/Projects/Adajoon/.cursor/skills/CLAUDE.md`  
**Size**: 925 lines, 23KB  
**Purpose**: Comprehensive reference for direct Claude conversations

**Used by**:
- Cursor with @-mentions: `@.cursor/skills/CLAUDE.md`
- Direct Claude conversations (copy/paste sections)
- Any editor with Claude integration

**Content**:
- Complete patterns from all 7 skills
- Searchable sections with anchors
- Links to full skill files
- Common scenarios with examples
- Quick pattern lookup table

**Format**: Optimized for human reading and @-mentions
- Table of contents with jump links
- Expandable sections
- Scenario-based examples
- Cross-references between sections

---

### 3. Updated README.md
**Location**: `/Users/khashsarrafi/Projects/Adajoon/README.md`  
**Purpose**: Explain how to use skills in different contexts

**Added section**: "Using Skills"
- How skills work in Cursor Agent (automatic)
- How to use in Composer/Chat (@ mentions)
- How to use in direct Claude conversations (copy/paste)
- Quick pattern lookup table
- Skill update process

---

### 4. Updated Skills README
**Location**: `/Users/khashsarrafi/Projects/Adajoon/.cursor/skills/README.md`  
**Purpose**: Document the unified system in skills directory

**Added**:
- Usage instructions for each context
- Explanation of unified system
- References to `.cursorrules` and `CLAUDE.md`

---

## How It Works

```
┌─────────────────────────────────────────────────┐
│  Single Source of Truth                         │
│  .cursor/skills/adajoon-{name}/SKILL.md         │
│  (~2,867 lines across 7 skills)                 │
└────────────┬────────────────────────────────────┘
             │
             ├──────────────┬──────────────┬
             │              │              │
             ▼              ▼              ▼
    ┌────────────┐  ┌─────────────┐  ┌──────────────┐
    │ .cursorrules│  │  CLAUDE.md  │  │ Cursor Agent │
    │            │  │             │  │              │
    │ 317 lines  │  │  925 lines  │  │ Auto-loads   │
    │ Concise    │  │ Comprehensive│  │ SKILL.md     │
    │ Quick ref  │  │ For @mentions│  │ files        │
    └────────────┘  └─────────────┘  └──────────────┘
         │                │                  │
         ▼                ▼                  ▼
    Composer/Chat    Direct Claude      Agent Mode
```

### Synchronization

All three formats reference the same underlying content in `.cursor/skills/`. When you update a skill file, all formats benefit:

1. **Update a skill**: Edit `.cursor/skills/adajoon-{name}/SKILL.md`
2. **Optionally update summaries**:
   - Update `.cursorrules` if it's a critical/frequently-used pattern
   - Update `CLAUDE.md` if it's a complex pattern needing detailed explanation
3. **All contexts benefit**: Cursor Agent, Composer, Chat, and direct Claude conversations

---

## Usage Examples

### Cursor Agent Mode
```
// Just start coding - skills auto-load based on file context
// Working on backend/app/routers/auth.py?
// → adajoon-backend, adajoon-security, adajoon-database automatically apply
```

### Cursor Composer Mode
```
// Press Cmd+I in any file
// Quick rules from .cursorrules automatically apply

// For detailed guidance:
@.cursor/skills/CLAUDE.md review my authentication code

// For specific skill:
@.cursor/skills/adajoon-backend/SKILL.md how do I structure this API?
```

### Cursor Chat Mode
```
// Press Cmd+L to open chat
// Reference comprehensive guide:
@.cursor/skills/CLAUDE.md what are the CSRF protection rules?

// Or reference specific sections:
@.cursor/skills/CLAUDE.md show me the backend router structure pattern
```

### Direct Claude Conversations (Outside Cursor)
```
// Open .cursor/skills/CLAUDE.md
// Find the section you need (use Cmd/Ctrl+F)
// Copy that section into your Claude conversation

Example prompt:
"I'm working on authentication in Adajoon. Here are the security patterns:

[Paste Security section from CLAUDE.md]

Please review my code against these patterns..."
```

---

## Maintenance

### When to Update `.cursorrules`

Update when:
- A new critical pattern emerges (e.g., new security requirement)
- A pattern is violated frequently (needs reinforcement)
- A file-specific trigger needs to be added
- A common anti-pattern needs highlighting

**Keep it concise**: Only the most essential rules. Full details go in individual SKILL.md files.

### When to Update `CLAUDE.md`

Update when:
- A skill file gets major updates (new sections, patterns)
- Common scenarios change (e.g., new deployment architecture)
- Cross-references need updating (e.g., new skill added)
- Quick lookup table needs new entries

**Keep it comprehensive**: Include enough detail to answer common questions without referencing full skills.

### When to Update Individual Skills

Update when:
- Bug fixed (document the fix)
- New pattern emerges (add with examples)
- Existing pattern clarified (add anti-patterns, edge cases)
- Version bump (update changelog)

See `.cursor/skills/adajoon-skill-improvement/SKILL.md` for full process.

---

## Benefits

### Before (Cursor Agent Only)
- ✅ Skills worked great in Cursor Agent mode
- ❌ No quick reference for Composer/Chat
- ❌ Direct Claude conversations required manual lookup
- ❌ No concise summary for fast scanning

### After (Unified System)
- ✅ Skills work in Cursor Agent mode (unchanged)
- ✅ Quick rules available in Composer/Chat via `.cursorrules`
- ✅ Comprehensive reference for @ mentions via `CLAUDE.md`
- ✅ Direct Claude conversations have copy/paste guide
- ✅ Single source of truth (`.cursor/skills/*.md`)
- ✅ Documented in main README for discoverability

---

## Quick Reference

| Context | File | Usage |
|---------|------|-------|
| Cursor Agent | `.cursor/skills/adajoon-{name}/SKILL.md` | Auto-loads based on file context |
| Cursor Composer/Chat | `.cursorrules` | Auto-applied quick rules |
| Cursor Composer/Chat | `CLAUDE.md` | Use `@.cursor/skills/CLAUDE.md` |
| Direct Claude | `CLAUDE.md` | Copy/paste relevant sections |

---

## Statistics

### Coverage
- **7 skills** covering all aspects of Adajoon codebase
- **~2,867 lines** of detailed guidelines in individual skills
- **317 lines** of concise rules in `.cursorrules`
- **925 lines** of comprehensive reference in `CLAUDE.md`

### File Sizes
- `.cursorrules`: 9.1KB (fast loading)
- `CLAUDE.md`: 23KB (comprehensive but manageable)
- Individual skills: 404-940 lines each

---

## Future Enhancements

### Potential Additions
1. **Auto-sync script**: Automatically update `.cursorrules` and `CLAUDE.md` when skills change
2. **Validation script**: Check that all patterns in `.cursorrules` exist in full skills
3. **Analytics**: Track which patterns are violated most (feed into skill-improvement process)
4. **VS Code extension**: Make skills available in non-Cursor editors

### Monitoring
- Track usage of `.cursorrules` (Cursor automatically uses it)
- Track @ mentions of `CLAUDE.md` (check Cursor logs)
- Track skill violations (weekly reviews)
- Measure bug prevention (monthly audits)

---

## Version History

- **v1.0** (2026-04-04): Initial unified system created
  - Created `.cursorrules` with concise rules
  - Created `CLAUDE.md` with comprehensive reference
  - Updated README.md with usage guide
  - Updated skills README with unified system docs

---

## Questions?

For questions about:
- **How to use skills**: See main `README.md` → "Using Skills" section
- **What each skill covers**: See `.cursor/skills/README.md`
- **How to improve skills**: See `.cursor/skills/adajoon-skill-improvement/SKILL.md`
- **Technical implementation**: This file (you're reading it)

---

**Created by**: Claude (Sonnet 4.5) via Cursor Agent  
**Date**: April 4, 2026  
**Purpose**: Make Adajoon coding skills accessible across all AI assistant contexts
