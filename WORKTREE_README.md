# 🚀 Worktree Setup System

You now have a complete automated system for creating isolated git worktrees with all dependencies pre-configured!

## What You Get

✅ **Automated git worktree creation** with custom branch names
✅ **Isolated Python venv** per worktree (no dependency conflicts)
✅ **All backend dependencies** installed via pip
✅ **All admin frontend** dependencies installed via npm
✅ **All mobile app** dependencies installed via npm
✅ **Ready-to-run** - just execute `./start.sh` when done

## Files Created

| File | Purpose |
|------|---------|
| `setup_worktree.sh` | Main automation script (executable) |
| `WORKTREE_SETUP.md` | Comprehensive guide with examples and troubleshooting |
| `WORKTREE_CHEATSHEET.md` | Quick reference for common commands |
| `WORKTREE_README.md` | This file - overview and getting started |

## 30-Second Quick Start

```bash
# 1. From your main repo directory, run:
./setup_worktree.sh feature/my-awesome-feature

# 2. Navigate to the created worktree:
cd ../feature/my-awesome-feature

# 3. Start developing:
./start.sh

# Services start automatically:
# - Backend API on http://localhost:8000
# - Admin Dashboard on http://localhost:3000
# - Mobile app development server
# - Redis server for task queue
```

## What The Script Does

When you run `./setup_worktree.sh feature/my-branch`, the script:

1. **Creates a git worktree** with a new branch
2. **Initializes a Python venv** in `backend/venv/`
3. **Installs backend dependencies** from `requirements.txt`
4. **Installs admin dashboard** Node modules
5. **Installs mobile app** Node modules

Total time: ~5-15 minutes (depending on your internet speed)

## Usage Examples

### Basic Usage (Default Path)
```bash
./setup_worktree.sh feature/user-authentication
# Creates: ../feature/user-authentication
```

### Custom Path
```bash
./setup_worktree.sh bugfix/database-bug ~/worktrees/db-fix
# Creates: ~/worktrees/db-fix
```

### iOS Prebuild (Optional - Background)
```bash
./setup_worktree.sh feature/my-feature ~/my-worktrees/feature --ios-prebuild
# Creates worktree AND starts iOS prebuild in background
# Prebuild log: ~/my-worktrees/feature/ios_prebuild.log
```

With the `--ios-prebuild` flag, the iOS native project (`ios/` folder) is built in the background while you work. This means:
- ✅ Setup completes immediately (doesn't wait for prebuild)
- ✅ iOS app is ready faster when you run `./start.sh`
- ✅ Native iOS project gets cached for subsequent runs
- ℹ️ Build takes ~5-10 minutes in background

### Branch with Hierarchy
```bash
./setup_worktree.sh feature/backend/cache-optimization ~/my-work/cache
# Creates: ~/my-work/cache with branch name feature/backend/cache-optimization
```

## Key Features

### ✨ Isolated Environments
Each worktree has its own:
- Git branch
- Python virtual environment (`backend/venv/`)
- Node modules (no conflicts between worktrees)
- `.env` configuration files

### 🔄 Easy Switching
```bash
# Work on feature 1
cd ../feature/feature1
./start.sh

# Stop services (Ctrl+C)
# Switch to feature 2
cd ../feature/feature2
./start.sh
```

### 🗑️ Simple Cleanup
```bash
# From main repo
git worktree remove /path/to/worktree
git worktree prune
```

### ⚙️ Environment Configuration (.env)
The script automatically handles `.env` files:
- ✅ Copies `.env` from main repo to worktree root
- ✅ Creates symlink at `backend/.env` → `../.env`
- ✅ Falls back to `env.example` if `.env` doesn't exist
- 💡 Share config across worktrees via the root `.env`

## Service URLs

After running `./start.sh`:

| Service | URL |
|---------|-----|
| **Backend API** | http://localhost:8000 |
| **API Documentation** | http://localhost:8000/docs |
| **Admin Dashboard** | http://localhost:3000 |
| **Expo Dev Server** | http://localhost:8082 |
| **Redis** | localhost:6379 |

## Common Workflows

### Development Workflow
```bash
# 1. Create worktree
./setup_worktree.sh feature/new-feature

# 2. Navigate and start
cd ../feature/new-feature
./start.sh

# 3. Make changes
# 4. Git commit and push
git add .
git commit -m "Add awesome feature"
git push origin feature/new-feature

# 5. Create pull request
# 6. When done, remove worktree
cd /path/to/main/repo
git worktree remove /path/to/worktree
```

### Testing Multiple Features
```bash
# Terminal 1: Feature A
./setup_worktree.sh feature/component-a
cd ../feature/component-a && ./start.sh

# Terminal 2: Feature B (while feature A is running)
./setup_worktree.sh feature/component-b
cd ../feature/component-b && ./start.sh

# Both can run simultaneously with different ports and databases!
```

### Keeping Up to Date
```bash
cd /path/to/worktree
git fetch origin
git pull origin main  # or git rebase origin/main
```

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| Python not found | `python3 --version` (need 3.11+) |
| npm install fails | `npm cache clean --force` then retry |
| Port conflicts | Kill the process: `lsof -ti:3000 \| xargs kill -9` |
| venv activation fails | Manually source: `source backend/venv/bin/activate` |

For more help, see **`WORKTREE_SETUP.md`** (comprehensive guide).

## Quick Reference

For fast lookups, see **`WORKTREE_CHEATSHEET.md`** which includes:
- Command cheat sheet
- Service URLs
- Service management
- Environment setup
- Pro tips

## Directory Layout After Setup

```
my-project/                    # Main repo (on main branch)
├── setup_worktree.sh          # The script
├── WORKTREE_SETUP.md          # Full documentation
├── WORKTREE_CHEATSHEET.md     # Quick reference
├── backend/
├── admin/
├── mobile/
└── ...

../feature/my-feature/         # Created by script
├── backend/
│   ├── venv/                  # ← Python virtual environment
│   ├── server.py
│   └── ...
├── admin/
│   ├── node_modules/          # ← Admin dependencies
│   └── ...
├── mobile/
│   ├── node_modules/          # ← Mobile dependencies
│   └── ...
└── start.sh                   # Works just like main repo
```

## System Requirements

Before using the script, ensure you have:

- ✅ **Git** with worktree support (any recent version)
- ✅ **Python 3.11+** (`python3 --version`)
- ✅ **Node.js 18+** (`node --version`)
- ✅ **npm 9+** (`npm --version`)
- ✅ **PostgreSQL** 12+ (for database operations)

## Pro Tips

### 1. Create an Alias
Add to your shell config (`.bashrc`, `.zshrc`, etc.):
```bash
alias new-worktree='./setup_worktree.sh'
# Then use: new-worktree feature/my-feature
```

### 2. Organize Worktrees
```bash
mkdir -p ~/worktrees
./setup_worktree.sh feature/ui-redesign ~/worktrees/ui
./setup_worktree.sh bugfix/bug-123 ~/worktrees/bug123
```

### 3. Monitor Multiple Worktrees
```bash
tmux new-session -d -s work1 -c ~/worktrees/feature1 './start.sh'
tmux new-session -d -s work2 -c ~/worktrees/feature2 './start.sh'
tmux list-sessions  # See both running
```

### 4. Update from Main
```bash
cd /path/to/worktree
git fetch origin
git rebase origin/main  # Sync with latest main
```

## Next Steps

1. **Review the Quick Reference**: Open `WORKTREE_CHEATSHEET.md` for a handy reference
2. **Read Full Documentation**: Open `WORKTREE_SETUP.md` for comprehensive guide
3. **Create Your First Worktree**: Run `./setup_worktree.sh feature/my-first-feature`
4. **Start Developing**: `cd ../feature/my-first-feature && ./start.sh`

## Support

- 📖 Full Guide: `WORKTREE_SETUP.md`
- ⚡ Quick Reference: `WORKTREE_CHEATSHEET.md`
- 🔨 Script: `setup_worktree.sh`
- 🚀 Main Startup: `start.sh --help`

---

**Ready to get started?** Run `./setup_worktree.sh feature/my-feature` and you're ready to code! 🎉
