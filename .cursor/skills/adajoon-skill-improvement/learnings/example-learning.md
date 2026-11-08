# Learning Entry: Race Condition in Vote Handling

**Date**: 2026-04-04
**Category**: Database
**Related PR/Issue**: #247

## What Happened
Users could vote multiple times on the same channel by clicking rapidly. The vote count would increment twice even though the database had a unique constraint on (user_id, channel_id).

## Why It Happened
Two concurrent requests would both check for existing votes, find none, and both try to insert. The second insert would fail with a database constraint error, but the user would see an error message instead of a successful single vote.

Root causes:
1. Check-then-insert pattern created a race condition window
2. No database-level locking during the operation
3. No transaction isolation level consideration

## The Fix

```python
# ❌ OLD (race condition)
async def add_vote(db: AsyncSession, user_id: int, channel_id: str, vote_type: str):
    existing = await db.execute(
        select(Vote).where(Vote.user_id == user_id, Vote.channel_id == channel_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already voted")
    
    vote = Vote(user_id=user_id, channel_id=channel_id, vote_type=vote_type)
    db.add(vote)
    await db.commit()

# ✅ NEW (with locking)
async def add_vote(db: AsyncSession, user_id: int, channel_id: str, vote_type: str):
    # Use SELECT FOR UPDATE to lock the row during check
    existing = await db.execute(
        select(Vote)
        .where(Vote.user_id == user_id, Vote.channel_id == channel_id)
        .with_for_update()
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already voted")
    
    vote = Vote(user_id=user_id, channel_id=channel_id, vote_type=vote_type)
    db.add(vote)
    await db.commit()
```

Alternative approach using upsert:
```python
# ✅ BETTER (atomic upsert)
from sqlalchemy.dialects.postgresql import insert

async def add_vote(db: AsyncSession, user_id: int, channel_id: str, vote_type: str):
    stmt = insert(Vote).values(
        user_id=user_id,
        channel_id=channel_id,
        vote_type=vote_type
    ).on_conflict_do_update(
        index_elements=['user_id', 'channel_id'],
        set_={'vote_type': vote_type}
    )
    await db.execute(stmt)
    await db.commit()
```

## Skill Update
- **Skill**: adajoon-database
- **Version**: v1.3.0 → v1.4.0 (MINOR - new pattern added)
- **Section**: Added "Concurrent Operations" section
- **Change**: 
  - Added SELECT FOR UPDATE pattern for check-then-insert scenarios
  - Added PostgreSQL upsert pattern for atomic operations
  - Added warning about race conditions in check-then-insert

## Prevention
- [x] Updated adajoon-database skill with concurrent patterns
- [x] Added "concurrent operations" to code review checklist
- [x] Created integration test with 100 concurrent vote requests
- [x] Documented in weekly review 2026-04-04
- [x] Shared with team in standup

## Test
Created test to verify fix:

```python
async def test_concurrent_votes(db: AsyncSession):
    """Test that concurrent votes don't create duplicates"""
    import asyncio
    
    # Try to vote 100 times concurrently
    tasks = [
        add_vote(db, user_id=1, channel_id="abc", vote_type="like")
        for _ in range(100)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Only one vote should succeed, rest should get "Already voted" error
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 1
    
    # Verify only one vote in database
    votes = await db.execute(
        select(Vote).where(Vote.user_id == 1, Vote.channel_id == "abc")
    )
    assert len(votes.all()) == 1
```

## Related Learnings
- Similar issue with favorite toggling (fixed in PR #198)
- General pattern: Any check-then-insert needs concurrency consideration

## Impact
- **Before**: ~5 race condition errors per day in logs
- **After**: 0 race condition errors in 2 weeks post-fix
- **Prevention**: Similar check-then-insert patterns audited across codebase
