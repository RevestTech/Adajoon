# Adajoon Cursor Skills

This directory contains Cursor Agent Skills that enforce project conventions and best practices for the Adajoon codebase.

## Available Skills

### 1. **adajoon-backend** (407 lines)
FastAPI backend patterns and conventions.

**Triggers**: Creating/editing backend routers, API endpoints, authentication code
**Covers**:
- Router structure with `/api/` prefix
- Cookie-based JWT authentication patterns
- CSRF protection for mutating endpoints
- Request logging with structured logging
- Redis caching patterns
- Database session management
- Response models and validation
- Rate limiting

### 2. **adajoon-frontend** (~400 lines)
React frontend patterns and conventions.

**Triggers**: Creating/editing React components, hooks, API clients
**Covers**:
- Custom hooks patterns (useAuth, useVotes, etc.)
- API calls using `authenticatedFetch` for mutations
- CSRF token handling
- OAuth integration (Google, Apple)
- Error handling and loading states
- localStorage patterns
- Environment variables (`import.meta.env.VITE_*`)

### 3. **adajoon-security** (531 lines)
Security best practices and patterns.

**Triggers**: Working with authentication, cookies, security headers, sensitive data
**Covers**:
- Security headers (COOP, COEP, CSP)
- Cookie attributes (httponly, secure, SameSite, domain)
- JWT secret management and validation
- CSRF token generation and verification
- OAuth redirect URI validation
- Stripe webhook signature verification
- Rate limiting
- Input validation and sanitization
- Secrets management
- CORS configuration

### 4. **adajoon-database** (404 lines)
Database models and Alembic migration patterns.

**Triggers**: Creating/editing models, migrations, database queries
**Covers**:
- SQLAlchemy model patterns
- Alembic migration patterns (**NEVER manual migrations in main.py**)
- Database session management
- Timestamp columns (DateTime with timezone, not strings)
- Foreign key constraints and indexes
- CHECK constraints for validation
- Migration file naming conventions
- Query optimization
- Transaction handling

### 5. **adajoon-deployment** (~450 lines)
Deployment patterns for Railway and Docker.

**Triggers**: Working with Dockerfiles, Railway config, nginx, deployment scripts
**Covers**:
- Railway dual-service architecture
- Docker multi-stage builds
- Environment variable configuration
- Frontend proxy pattern (backend proxies to frontend)
- Health check endpoints
- Structured logging (JSON in production)
- Database migrations on deployment
- SYNC_API_KEY for manual sync
- Build optimization

### 6. **adajoon-conventions** (435 lines)
Code quality and naming conventions.

**Triggers**: All code edits
**Covers**:
- Python: Type hints, async/await, f-strings, import organization
- JavaScript/React: const/let, arrow functions, naming conventions
- Comment guidelines (**NO obvious/redundant comments**)
- Error handling patterns
- File organization
- Environment variable usage
- API versioning
- Git commit message format (Conventional Commits)

## Total Coverage

- **~2,867 lines** of comprehensive guidelines
- **6 specialized skills** covering all aspects of the codebase
- **Auto-triggered** based on file context and user actions
- **Extracted from real codebase** patterns and conventions

## Usage

### Cursor Agent Mode (Automatic)
Skills are automatically activated by Cursor Agent when you work on relevant files or mention related keywords.

### Cursor Composer/Chat Mode
- Quick rules: Read from `../.cursorrules` at project root
- Detailed reference: Use `@.cursor/skills/CLAUDE.md` for comprehensive guidance
- Specific skills: Reference individual SKILL.md files with @ mentions

### Direct Claude Conversations (Outside Cursor)
- Copy relevant sections from `.cursor/skills/CLAUDE.md`
- Search for patterns you need (Cmd/Ctrl+F)
- Include in your conversation prompt

### What Skills Provide

1. **Pattern enforcement** - Ensures consistency across the codebase
2. **Best practices** - Prevents common mistakes and security issues
3. **Quick reference** - Code examples and checklists
4. **Anti-patterns** - What to avoid and why

### Unified System

This directory contains the source of truth. Other formats reference these skills:
- **`.cursorrules`** (project root) - Concise summary for Cursor's built-in rules
- **`CLAUDE.md`** (this directory) - Comprehensive reference for direct Claude conversations

## Maintenance

When updating project conventions:
1. Update the relevant skill file
2. Test with example code
3. Commit changes to version control
4. Skills are automatically reloaded by Cursor

## Version

Created for Adajoon v2.3.0 (April 2026)
