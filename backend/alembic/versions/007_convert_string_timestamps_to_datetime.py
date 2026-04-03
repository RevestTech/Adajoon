"""Convert string timestamp columns to DateTime with timezone

Revision ID: 007
Revises: 006
Create Date: 2026-04-03 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert Channel timestamp fields from VARCHAR to TIMESTAMPTZ
    # Note: We use ALTER COLUMN with USING to convert existing data
    # Empty strings will be converted to NULL
    
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
        USING CASE 
            WHEN updated_at = '' OR updated_at IS NULL THEN NULL 
            ELSE to_timestamp(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN health_checked_at TYPE TIMESTAMPTZ 
        USING CASE 
            WHEN health_checked_at = '' OR health_checked_at IS NULL THEN NULL 
            ELSE to_timestamp(health_checked_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN last_validated_at TYPE TIMESTAMPTZ 
        USING CASE 
            WHEN last_validated_at = '' OR last_validated_at IS NULL THEN NULL 
            ELSE to_timestamp(last_validated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    # Convert RadioStation timestamp fields
    op.execute('''
        ALTER TABLE radio_stations 
        ALTER COLUMN health_checked_at TYPE TIMESTAMPTZ 
        USING CASE 
            WHEN health_checked_at = '' OR health_checked_at IS NULL THEN NULL 
            ELSE to_timestamp(health_checked_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    # Convert Stream timestamp fields
    op.execute('''
        ALTER TABLE streams 
        ALTER COLUMN added_at TYPE TIMESTAMPTZ 
        USING CASE 
            WHEN added_at = '' OR added_at IS NULL THEN NULL 
            ELSE to_timestamp(added_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    # Set default values for new records
    op.execute('ALTER TABLE channels ALTER COLUMN updated_at SET DEFAULT NULL;')
    op.execute('ALTER TABLE channels ALTER COLUMN health_checked_at SET DEFAULT NULL;')
    op.execute('ALTER TABLE channels ALTER COLUMN last_validated_at SET DEFAULT NULL;')
    op.execute('ALTER TABLE radio_stations ALTER COLUMN health_checked_at SET DEFAULT NULL;')
    op.execute('ALTER TABLE streams ALTER COLUMN added_at SET DEFAULT NULL;')


def downgrade() -> None:
    # Downgrade is risky as we may lose precision
    # Convert back to VARCHAR(50) with ISO format
    
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN updated_at TYPE VARCHAR(50) 
        USING CASE 
            WHEN updated_at IS NULL THEN '' 
            ELSE to_char(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN health_checked_at TYPE VARCHAR(50) 
        USING CASE 
            WHEN health_checked_at IS NULL THEN '' 
            ELSE to_char(health_checked_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('''
        ALTER TABLE channels 
        ALTER COLUMN last_validated_at TYPE VARCHAR(50) 
        USING CASE 
            WHEN last_validated_at IS NULL THEN '' 
            ELSE to_char(last_validated_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('''
        ALTER TABLE radio_stations 
        ALTER COLUMN health_checked_at TYPE VARCHAR(50) 
        USING CASE 
            WHEN health_checked_at IS NULL THEN '' 
            ELSE to_char(health_checked_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    op.execute('''
        ALTER TABLE streams 
        ALTER COLUMN added_at TYPE VARCHAR(50) 
        USING CASE 
            WHEN added_at IS NULL THEN '' 
            ELSE to_char(added_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
        END;
    ''')
    
    # Set default values back to empty string
    op.execute('ALTER TABLE channels ALTER COLUMN updated_at SET DEFAULT \'\';')
    op.execute('ALTER TABLE channels ALTER COLUMN health_checked_at SET DEFAULT \'\';')
    op.execute('ALTER TABLE channels ALTER COLUMN last_validated_at SET DEFAULT \'\';')
    op.execute('ALTER TABLE radio_stations ALTER COLUMN health_checked_at SET DEFAULT \'\';')
    op.execute('ALTER TABLE streams ALTER COLUMN added_at SET DEFAULT \'\';')
