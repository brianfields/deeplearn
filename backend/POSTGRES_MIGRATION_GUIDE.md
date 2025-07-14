# PostgreSQL Migration Guide

This guide walks you through migrating the DeepLearn system from SQLite to PostgreSQL.

## Prerequisites

1. **PostgreSQL installed** (version 12 or later)
2. **Python dependencies updated** (already done via requirements.txt)
3. **Database credentials** ready

## Step 1: Install and Setup PostgreSQL

### On macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql

# Create database and user
createdb deeplearn
createuser --interactive deeplearn_user
```

### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres createdb deeplearn
sudo -u postgres createuser --interactive deeplearn_user
```

### On Windows:
Download and install PostgreSQL from https://www.postgresql.org/download/windows/

## Step 2: Configure Database Connection

Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration (choose one method)

# Method 1: Full DATABASE_URL (recommended)
DATABASE_URL=postgresql://username:password@localhost:5432/deeplearn

# Method 2: Individual components
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=deeplearn
DATABASE_USER=username
DATABASE_PASSWORD=password

# Optional: Enable SQL logging for debugging
DATABASE_ECHO=false
```

Replace `username` and `password` with your actual PostgreSQL credentials.

## Step 3: Install Updated Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `psycopg2-binary` (PostgreSQL adapter)
- `alembic` (database migrations)

## Step 4: Initialize Database Schema

Run the initial database migration to create tables:

```bash
cd backend

# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration to create tables
alembic upgrade head
```

## Step 5: Migrate Existing Data

Use the migration script to move your existing data:

```bash
cd backend

# Dry run to see what will be migrated
python migrate_to_postgres.py --dry-run

# Create backup and migrate (recommended)
python migrate_to_postgres.py --backup

# Or migrate without backup
python migrate_to_postgres.py
```

The migration script will:
- ✅ Backup existing SQLite data
- ✅ Migrate learning paths from JSON files
- ✅ Migrate bite-sized topics from SQLite
- ✅ Migrate all components
- ✅ Verify migration success

## Step 6: Update Application Code

### Server Configuration
The server startup has been updated to use `DatabaseService` instead of `SimpleStorage`. However, you may need to update the conversation engine integration.

### CLI Scripts
Update your CLI scripts to use PostgreSQL instead of SQLite. Replace:

```python
# Old SQLite approach
import sqlite3
conn = sqlite3.connect("bite_sized_topics.db")
```

With:

```python
# New PostgreSQL approach
from database_service import get_database_service
db_service = get_database_service()
```

## Step 7: Test the Migration

1. **Start the server:**
   ```bash
   cd backend
   python -m src.api.server
   ```

2. **Test API endpoints:**
   ```bash
   curl http://localhost:8000/api/progress
   curl http://localhost:8000/api/learning-paths
   ```

3. **Test learning path creation:**
   ```bash
   curl -X POST http://localhost:8000/api/start-topic \
        -H "Content-Type: application/json" \
        -d '{"topic": "Test Topic", "user_level": "beginner"}'
   ```

## Step 8: Verify Data Integrity

Check that your data was migrated correctly:

```bash
# Check learning paths
python -c "
from src.database_service import get_database_service
db = get_database_service()
paths = db.get_all_learning_paths()
print(f'Found {len(paths)} learning paths')
"

# Check bite-sized topics
python -c "
from src.database_service import get_database_service
from sqlalchemy import select, func
from src.data_structures import BiteSizedTopic, BiteSizedComponent

db = get_database_service()
with db.get_session() as session:
    topic_count = session.execute(select(func.count(BiteSizedTopic.id))).scalar()
    component_count = session.execute(select(func.count(BiteSizedComponent.id))).scalar()
    print(f'Found {topic_count} topics and {component_count} components')
"
```

## Troubleshooting

### Connection Issues

**Error: `FATAL: database "deeplearn" does not exist`**
```bash
createdb deeplearn
```

**Error: `FATAL: role "username" does not exist`**
```bash
createuser username
# Grant permissions
psql -d deeplearn -c "GRANT ALL PRIVILEGES ON DATABASE deeplearn TO username;"
```

**Error: `FATAL: password authentication failed`**
- Check your `.env` file credentials
- Verify PostgreSQL user password: `psql -U username -d deeplearn`

### Migration Issues

**Error: `No SQLite database found`**
- Ensure you have existing `bite_sized_topics.db` file
- Run from the correct directory (backend/)

**Error: `No learning data directory found`**
- Ensure you have `.learning_data/` directory with JSON files
- Check permissions

### Alembic Issues

**Error: `Target database is not up to date`**
```bash
alembic upgrade head
```

**Error: `Can't locate revision identified by 'head'`**
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Performance Considerations

### Indexing
The PostgreSQL schema includes appropriate indexes for:
- Bite-sized topics (core_concept, user_level, creation_strategy)
- Components (topic_id, component_type)
- Learning paths (user_id)

### Connection Pooling
The database service is configured with connection pooling:
- Pool size: 5 connections
- Max overflow: 10 connections
- Pool recycle: 1 hour

### Query Optimization
- Use `select()` statements instead of raw SQL
- Leverage SQLAlchemy's lazy loading for relationships
- Consider adding indexes for frequently queried columns

## Backup and Maintenance

### Regular Backups
```bash
# Backup database
pg_dump deeplearn > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql deeplearn < backup_file.sql
```

### Database Maintenance
```bash
# Analyze tables for query planning
psql -d deeplearn -c "ANALYZE;"

# Vacuum to reclaim space
psql -d deeplearn -c "VACUUM;"
```

## Next Steps

1. **Archive old files:** Once migration is verified, archive or remove:
   - `bite_sized_topics.db`
   - `.learning_data/` directory (if desired)

2. **Update documentation:** Update any documentation that references SQLite

3. **Monitor performance:** Watch query performance and optimize as needed

4. **Set up monitoring:** Consider tools like PostgreSQL's built-in stats or external monitoring

## Rollback Plan

If you need to rollback to SQLite:

1. **Stop the application**
2. **Restore from backup:**
   ```bash
   cp migration_backup/bite_sized_topics_*.db bite_sized_topics.db
   cp -r migration_backup/learning_data_* .learning_data/
   ```
3. **Revert code changes** (restore SimpleStorage usage)
4. **Update configuration** (remove DATABASE_* variables)

The migration script creates automatic backups to make rollback easy if needed.