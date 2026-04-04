---
name: adajoon-database
description: Enforces Adajoon database patterns for SQLAlchemy models, Alembic migrations, session management, and query optimization. Use when creating or editing models, writing migrations, working with database queries, or when the user mentions database, models, migrations, Alembic, SQLAlchemy, or database patterns.
---

# Adajoon Database Patterns

**Version**: 1.0.0 (Updated: 2026-04-04)

## Changelog
- v1.0.0 (2026-04-04): Initial versioning - established baseline database patterns

## Core Principles

**CRITICAL**: NEVER manually create tables in `main.py` or application code. ALWAYS use Alembic migrations for schema changes.

## SQLAlchemy Model Patterns

### Base Model Structure

```python
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Index, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class ModelName(Base):
    __tablename__ = "table_name"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # columns, relationships, __table_args__ here
```

### Timestamp Columns

**CRITICAL**: Use `DateTime(timezone=True)` ALWAYS, NEVER strings.

```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
optional_at = Column(DateTime(timezone=True), nullable=True)
```

### Primary Keys

```python
id = Column(Integer, primary_key=True, autoincrement=True)  # Default
id = Column(String, primary_key=True)  # For external IDs
code = Column(String(10), primary_key=True)  # Natural key
```

### Foreign Keys and Relationships

```python
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

# Parent side
items = relationship("Child", back_populates="parent", cascade="all, delete-orphan")

# Child side
parent = relationship("Parent", back_populates="items")
```

### Indexes

```python
# Single column
email = Column(String(320), unique=True, index=True)

# Composite indexes
__table_args__ = (
    Index("ix_composite", "col1", "col2", "col3"),
    Index("ix_unique", "col1", "col2", unique=True),
)
```

### Column Types

- Short text: `String(255)`
- Email: `String(320)`
- Long text/URLs/JSON: `Text`
- Flags: `Boolean, default=False`
- Numbers: `Integer`
- Timestamps: `DateTime(timezone=True)` with `server_default=func.now()`

### Enums: Use String + CHECK Constraint

```python
# Model
subscription_tier = Column(String(50), default="free")

# Migration
op.execute("ALTER TABLE users ADD CONSTRAINT check_tier CHECK (subscription_tier IN ('free', 'plus', 'pro'))")
```

## Alembic Migration Patterns

### Migration File Naming

Format: `NNN_descriptive_name.py` where NNN is a 3-digit revision ID:

```
001_initial_schema.py
002_add_watch_history.py
003_add_playlists.py
004_add_parental_controls.py
```

### Migration File Template

```python
"""Brief description of what this migration does

Revision ID: 001
Revises: None
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None  # or previous revision like '000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migration code here
    pass


def downgrade() -> None:
    # Rollback code here
    pass
```

### Creating Tables in Migrations

**Use `CREATE TABLE IF NOT EXISTS` pattern:**

```python
def upgrade() -> None:
    op.execute('''
        CREATE TABLE IF NOT EXISTS table_name (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    ''')
    
    # Create indexes
    op.execute('CREATE INDEX IF NOT EXISTS ix_table_user_id ON table_name (user_id);')
    op.execute('CREATE INDEX IF NOT EXISTS ix_table_is_active ON table_name (is_active);')
```

### Adding Columns

```python
def upgrade() -> None:
    op.execute('''
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS kids_mode_enabled BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS parental_pin_hash VARCHAR(255) DEFAULT '';
    ''')
```

### Converting Column Types

```python
def upgrade() -> None:
    # Convert string timestamps to DateTime with timezone
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
        USING CASE 
            WHEN updated_at = '' OR updated_at IS NULL THEN NULL 
            ELSE to_timestamp(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('ALTER TABLE channels ALTER COLUMN updated_at SET DEFAULT NULL;')
```

### Adding CHECK Constraints

```python
def upgrade() -> None:
    # Enum validation
    op.execute('''
        ALTER TABLE users
        ADD CONSTRAINT check_subscription_tier 
        CHECK (subscription_tier IN ('free', 'plus', 'pro', 'family'));
    ''')
    
    # Value range validation
    op.execute('''
        ALTER TABLE watch_history
        ADD CONSTRAINT check_duration_seconds 
        CHECK (duration_seconds >= 0);
    ''')
```

### Creating Indexes

```python
def upgrade() -> None:
    # Standard B-tree index
    op.execute('CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);')
    
    # Composite index
    op.execute('CREATE INDEX IF NOT EXISTS ix_composite ON table_name (col1, col2, col3);')
    
    # Unique composite index
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_unique ON table_name (col1, col2);')
    
    # GIN index for full-text search (requires pg_trgm extension)
    op.execute('CREATE INDEX IF NOT EXISTS ix_name_gin_trgm ON table_name USING gin (name gin_trgm_ops);')
```

### Downgrade Pattern

**ALWAYS implement proper downgrade:**

```python
def downgrade() -> None:
    # Drop in reverse order of upgrade
    op.execute('DROP INDEX IF EXISTS ix_table_is_active;')
    op.execute('DROP INDEX IF EXISTS ix_table_user_id;')
    op.execute('DROP TABLE IF EXISTS table_name;')
```

### Migration Checklist

When creating a migration:

- [ ] Use sequential 3-digit revision ID
- [ ] Set correct `down_revision` to chain migrations
- [ ] Use `op.execute()` with `IF NOT EXISTS` / `IF EXISTS`
- [ ] Create indexes for foreign keys
- [ ] Add CHECK constraints for enums
- [ ] Use `TIMESTAMPTZ` for all timestamps
- [ ] Implement complete downgrade function
- [ ] Test both upgrade and downgrade

## Database Session Management

Use `get_db()` dependency from `app.database`:

```python
from app.database import get_db

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Model))
    return result.scalars().all()
```

## Query Patterns

```python
from sqlalchemy import select

# Select
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# Insert
db.add(User(email="user@example.com"))
await db.commit()

# Update
user.name = "New Name"
await db.commit()

# Delete
await db.delete(user)
await db.commit()

# Transaction
async with async_session() as session:
    try:
        session.add(obj1)
        await session.commit()
    except:
        await session.rollback()
        raise
```

## Optimization

**Index these:**
- Foreign keys (always)
- WHERE clause columns
- ORDER BY columns

**Full-text search (pg_trgm):**

```python
op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
op.execute('CREATE INDEX ix_name_trgm ON table USING gin (name gin_trgm_ops);')
```

**Tips:**
- Composite indexes for multi-column queries
- `selectinload()` for eager loading
- `limit()` for pagination


## Anti-Patterns to Avoid

### ❌ NEVER Do Manual Migrations

```python
# ❌ WRONG - Never in main.py or startup code
Base.metadata.create_all(bind=engine)
```

Use Alembic instead:

```bash
# ✅ CORRECT
alembic revision -m "add_new_table"
alembic upgrade head
```

### ❌ NEVER Use String for Timestamps

```python
# ❌ WRONG
updated_at = Column(String(50), default="")

# ✅ CORRECT
updated_at = Column(DateTime(timezone=True), server_default=func.now())
```

### ❌ NEVER Forget Timezone

```python
# ❌ WRONG
created_at = Column(DateTime, server_default=func.now())

# ✅ CORRECT
created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### ❌ NEVER Skip Foreign Key Index

```python
# ❌ WRONG - Missing index
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

# ✅ CORRECT
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
```

### ❌ NEVER Use SQLAlchemy Enum for String Enums

```python
# ❌ WRONG - Hard to change, migration complexity
from sqlalchemy import Enum
status = Column(Enum('active', 'inactive', name='status_enum'))

# ✅ CORRECT - Use String + CHECK constraint
status = Column(String(20), default='active')
# Add CHECK constraint in migration
```

## Quick Reference

### Creating a New Model

1. Add model class to `backend/app/models.py`
2. Create migration: `alembic revision -m "add_model_name"`
3. Write upgrade/downgrade in migration file
4. Run migration: `alembic upgrade head`
5. Test rollback: `alembic downgrade -1` then `alembic upgrade head`

### Adding a Column

1. Add column to model in `models.py`
2. Create migration: `alembic revision -m "add_column_name"`
3. Use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
4. Run migration: `alembic upgrade head`

### Migration Commands

```bash
# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```
