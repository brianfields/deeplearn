# Git Worktree Setup Guide

This document explains how to use the `setup_worktree.sh` script to quickly set up new git worktrees with all dependencies installed and ready to run.

## Overview

The `setup_worktree.sh` script automates the entire worktree setup process:

1. **Creates a git worktree** with a new branch
2. **Sets up Python venv** in the backend
3. **Installs backend dependencies** via pip
4. **Installs admin dashboard** dependencies via npm
5. **Installs mobile app** dependencies via npm
6. **Reports status** and provides next steps

## Prerequisites

Before using this script, ensure you have:

- **Git** (with worktree support)
- **Python 3.11+** (for backend)
- **Node.js 18+** and **npm** (for frontend/mobile)
- **PostgreSQL** (for database, if running with the full stack)
- All main branch dependencies installed in your primary repo

## Quick Start

### Basic Usage

```bash
# Create a worktree for a feature branch
./setup_worktree.sh feature/new-feature

# Create a worktree with a custom path
./setup_worktree.sh bugfix/issue-123 ~/code/worktrees/my-issue
```

### What Happens

1. The script creates a new worktree in `../feature/new-feature` (or your specified path)
2. Creates a fresh branch off the current branch
3. Sets up an isolated Python virtual environment in `backend/venv`
4. Installs all Python dependencies from `backend/requirements.txt`
5. Installs Node dependencies for admin dashboard
6. Installs Node dependencies for mobile app

### Using Your Worktree

Once setup completes successfully:

```bash
# Navigate to your worktree
cd ../feature/new-feature

# Start the full stack (backend, admin, mobile)
./start.sh

# Or start individual services
cd backend && source venv/bin/activate && python server.py
cd admin && npm run dev
cd mobile && npm start
```

## Examples

### Feature Branch with Default Path

```bash
./setup_worktree.sh feature/user-authentication
```

Creates: `../feature/user-authentication`

### Bug Fix with Custom Path

```bash
./setup_worktree.sh bugfix/database-connection ~/worktrees/db-fix
```

Creates: `~/worktrees/db-fix`

### Complex Feature

```bash
./setup_worktree.sh feature/learning-paths/advanced ~/code/branches/learning
```

Creates: `~/code/branches/learning` with branch `feature/learning-paths/advanced`

### iOS Prebuild (New Feature - Background Building)

Start iOS prebuild in the background while you work:

```bash
./setup_worktree.sh feature/my-feature ~/worktrees/my-feature --ios-prebuild
```

This will:
1. ✅ Create the worktree and install all dependencies
2. ✅ Start iOS prebuild (`npm run ios:prebuild`) in background
3. ✅ Complete immediately - you don't wait for the build
4. ✅ Build continues while you work on other things

**Monitoring the iOS prebuild:**

```bash
# Check if prebuild is still running
kill -0 <PID> && echo "Still running" || echo "Complete"

# View live build output
tail -f /path/to/worktree/ios_prebuild.log

# Kill the prebuild if needed
kill <PID>
```

The native iOS project will be built and cached at: `worktree/mobile/ios/`

This dramatically speeds up iOS development since:
- ✅ First `./start.sh` will use the prebuilt native project
- ✅ Subsequent runs are much faster
- ✅ You can start backend/admin development immediately
- ✅ iOS simulator is ready when you need it

## Environment Configuration (.env)

The script automatically handles environment variables across worktrees:

### How It Works

1. **Copies from main repo**: If `.env` exists in your main repo root, it's copied to the worktree root
2. **Creates symlink**: A symlink is created at `backend/.env` → `../.env` (the root .env)
3. **Fallback options**:
   - If no root `.env`, tries to copy from `backend/.env`
   - If that doesn't exist, uses `env.example` as a template

### Directory Structure After Setup

```
worktree-directory/
├── .env                        # ← Environment variables (copied from main repo)
├── backend/
│   └── .env → ../.env         # ← Symlink to root .env
└── ...
```

### Sharing Configuration

All worktrees use the **same `.env` file from your main repo**:

```bash
# Edit the shared config in main repo
cd /path/to/main/repo
vim .env
# Changes apply to all worktrees!

# Or edit per-worktree (if needed)
cd /path/to/worktree
vim .env
```

### What Gets Configured

Your `.env` file contains:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/deeplearn

# OpenAI / LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Redis (for task queue)
REDIS_URL=redis://localhost:6379/0

# Optional
USER_LEVEL=beginner
TEMPERATURE=0.7
DEBUG=false
```

### Typical Workflow

```bash
# 1. Main repo has your .env with API keys, etc.
cd /path/to/main/repo
cat .env
# DATABASE_URL=...
# OPENAI_API_KEY=...

# 2. Create worktree - .env is copied automatically
./setup_worktree.sh feature/my-feature

# 3. Worktree gets the same config
cd ../feature/my-feature
cat .env  # Same as main repo!
cat backend/.env  # Symlink points to root .env

# 4. Services use the config
./start.sh  # Backend reads from backend/.env (symlinked)
```

## Directory Structure

After setup, your worktree will have this structure:

```
worktree-directory/
├── backend/
│   ├── venv/                  # Python virtual environment (isolated)
│   ├── requirements.txt       # Python dependencies
│   ├── server.py
│   └── ... (other backend files)
├── admin/
│   ├── node_modules/          # Node dependencies
│   ├── package.json
│   └── ... (admin frontend)
├── mobile/
│   ├── node_modules/          # Node dependencies
│   ├── package.json
│   └── ... (mobile app)
├── start.sh                   # Startup script
└── ... (other root files)
```

## Service Details

### Backend
- **Location**: `backend/venv/bin/python`
- **Activation**: `source backend/venv/bin/activate`
- **Start**: `python server.py`
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### Admin Dashboard
- **Location**: `admin/`
- **Start**: `npm run dev`
- **URL**: http://localhost:3000
- **Technology**: Next.js + React

### Mobile App
- **Location**: `mobile/`
- **Start**: `npm start`
- **Technology**: React Native + Expo

## Common Workflows

### Switch Between Worktrees

```bash
# From primary repo (main branch)
cd /path/to/primary/repo

# Work on feature 1
cd ../feature/my-feature
./start.sh

# Stop services (Ctrl+C)

# Switch to another worktree
cd ../bugfix/issue-123
./start.sh
```

### Keep Worktree Up to Date

```bash
cd /path/to/worktree

# Fetch latest changes from main branch
git fetch origin

# Update your branch (if it's behind)
git pull origin main
```

### Delete a Worktree

```bash
# From primary repo
cd /path/to/primary/repo

# Remove the worktree
git worktree remove /path/to/worktree
```

## Environment Variables

Each worktree uses the same `.env` file locations as the primary repo. You can customize environment variables per worktree:

```bash
# Backend
cd /path/to/worktree/backend
cp .env.example .env
# Edit .env as needed

# Admin (if needed)
cd ../admin
# Create .env.local if needed
```

## Troubleshooting

### "Failed to create Python virtual environment"

**Cause**: Python 3.11+ not installed or not in PATH

**Solution**:
```bash
# Check Python version
python3 --version

# If needed, install or use specific Python path
python3.11 -m venv backend/venv
```

### "Failed to install backend dependencies"

**Cause**: Missing system dependencies or pip issues

**Solution**:
```bash
# Manually install with more verbose output
cd /path/to/worktree/backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -v
```

### "Failed to install admin dashboard dependencies"

**Cause**: Node.js 18+ not installed or npm issues

**Solution**:
```bash
cd /path/to/worktree/admin
npm install --verbose
# Or clear cache and retry
npm cache clean --force
npm install
```

### "Backend service won't start"

**Solution**:
```bash
cd /path/to/worktree/backend
source venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"
python server.py --verbose  # Run with verbose logging
```

### "Admin dashboard won't start"

**Solution**:
```bash
cd /path/to/worktree/admin
npm run dev -- --debug
# Check for port conflicts (port 3000 in use)
```

## Performance Tips

1. **Use separate worktrees for different tasks** - Avoids dependency conflicts
2. **Keep databases consistent** - Use same PostgreSQL database if possible
3. **Cache Node modules** - npm cache is shared, so first install is slowest
4. **Pre-install in main branch** - Dependencies download faster on subsequent worktrees

## Advanced Usage

### Create Worktree from Specific Branch

```bash
# First, ensure you're on the branch you want to base from
git checkout some-other-branch

# Then create the worktree
./setup_worktree.sh feature/new-approach
```

### Create Multiple Worktrees in Parallel

```bash
# Terminal 1
./setup_worktree.sh feature/component-a

# Terminal 2 (while first is running)
./setup_worktree.sh feature/component-b
```

### Sync with Main Branch

```bash
cd /path/to/worktree

# Update branch to latest main
git fetch origin
git rebase origin/main

# or merge
git pull origin main
```

## Cleanup

### Remove Unused Worktrees

```bash
# List all worktrees
git worktree list

# Remove a worktree
git worktree remove /path/to/worktree

# Remove with forced prune of stale entries
git worktree prune
```

## Tips & Tricks

1. **Alias the script** in your shell config:
   ```bash
   alias new-worktree='./setup_worktree.sh'
   # Then: new-worktree feature/my-feature
   ```

2. **Create a worktrees directory** to organize them:
   ```bash
   mkdir -p ~/worktrees
   ./setup_worktree.sh feature/ui-redesign ~/worktrees/ui
   ```

3. **Monitor multiple worktrees** with `tmux` or `screen`:
   ```bash
   tmux new-session -d -s worktree1 -c ~/worktrees/feature1 './start.sh'
   tmux new-session -d -s worktree2 -c ~/worktrees/feature2 './start.sh'
   ```

## Related Commands

```bash
# Check worktree status
git worktree list

# See which branch each worktree is on
git worktree list --porcelain

# Clean up stale worktree entries
git worktree prune

# Fix corrupted worktree references
git worktree repair
```

## Questions?

If you encounter issues or need help:

1. Check this troubleshooting section
2. Review the individual service documentation
3. Check `./start.sh --help` for startup options
4. Review backend, admin, and mobile README files
