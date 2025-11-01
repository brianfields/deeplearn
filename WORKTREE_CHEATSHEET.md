# Git Worktree Setup - Quick Reference

## ⚡ Quick Start

```bash
# Basic setup (creates worktree at ../feature/my-feature)
./setup_worktree.sh feature/my-feature

# Custom path
./setup_worktree.sh feature/my-feature ~/my-worktrees/feature1

# With iOS prebuild in background (setup completes immediately!)
./setup_worktree.sh feature/my-feature ~/my-worktrees/feature --ios-prebuild

# Start working
cd ../feature/my-feature
./start.sh
```

## 📋 Common Commands

| Task | Command |
|------|---------|
| **Create worktree** | `./setup_worktree.sh feature/name` |
| **List worktrees** | `git worktree list` |
| **Navigate to worktree** | `cd /path/to/worktree` |
| **Start all services** | `./start.sh` |
| **Start backend only** | `cd backend && source venv/bin/activate && python server.py` |
| **Start admin only** | `cd admin && npm run dev` |
| **Start mobile only** | `cd mobile && npm start` |
| **Remove worktree** | `git worktree remove /path/to/worktree` |
| **Clean up stale refs** | `git worktree prune` |

## 🎯 Service URLs

| Service | URL | Port |
|---------|-----|------|
| Backend API | `http://localhost:8000` | 8000 |
| API Docs | `http://localhost:8000/docs` | 8000 |
| Admin Dashboard | `http://localhost:3000` | 3000 |
| Mobile/Web | `http://localhost:8082` | 8082 |
| Redis | `localhost:6379` | 6379 |

## 🔧 Service Management

```bash
# View logs
tail -f worker.log              # ARQ worker logs
tail -f ~/.pm2/logs/*backend*   # Backend logs (if using PM2)

# Kill services (if stuck)
lsof -ti:8000 | xargs kill -9   # Kill backend
lsof -ti:3000 | xargs kill -9   # Kill admin
lsof -ti:6379 | xargs kill -9   # Kill Redis

# Start with flags
./start.sh --no-worker          # Skip ARQ worker
./start.sh --no-admin           # Skip admin dashboard
./start.sh --no-redis           # Skip Redis
./start.sh --web                # Include web app
```

## 📁 Directory Structure

```
worktree/
├── backend/venv/               # Python virtual environment
├── backend/requirements.txt    # Backend dependencies
├── admin/node_modules/         # Admin dependencies
├── mobile/node_modules/        # Mobile dependencies
├── start.sh                    # Main startup script
└── .git/                       # Git worktree reference
```

## 🚀 Typical Workflow

```bash
# 1. Create new worktree from main branch
./setup_worktree.sh feature/user-auth

# 2. Navigate to worktree
cd ../feature/user-auth

# 3. Start development
./start.sh

# 4. Make changes, commit, push
git add .
git commit -m "Add user authentication"
git push origin feature/user-auth

# 5. When done, remove worktree
cd /path/to/primary/repo
git worktree remove /path/to/worktree

# 6. Clean up
git worktree prune
```

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `Python not found` | Ensure Python 3.11+ installed: `python3 --version` |
| `npm install fails` | Clear cache: `npm cache clean --force` |
| `Port already in use` | Kill process: `lsof -ti:PORT \| xargs kill -9` |
| `Backend won't start` | Check venv: `source backend/venv/bin/activate` then `python server.py` |
| `Admin won't start` | Check Node.js: `node --version` and `npm install` |

## 📝 Environment Setup

```bash
# .env is AUTOMATICALLY copied from main repo!
# No manual setup needed.

# If you need to edit config:
cd /path/to/worktree
vim .env

# backend/.env is a symlink, so changes at root affect backend
cat backend/.env  # Shows root .env content
```

**Directory structure after setup:**
```
worktree/
├── .env          # ← Environment variables
├── backend/
│   └── .env → ../.env   # ← Symlink to root
└── ...
```

## 💡 Pro Tips

1. **Alias the script**: Add to shell config
   ```bash
   alias new-worktree='./setup_worktree.sh'
   new-worktree feature/my-feature
   ```

2. **Organize worktrees**: Create a worktrees directory
   ```bash
   mkdir -p ~/worktrees
   ./setup_worktree.sh feature/name ~/worktrees/name
   ```

3. **iOS Prebuild**: Start iOS prebuild in background
   ```bash
   ./setup_worktree.sh feature/name ~/worktrees/name --ios-prebuild
   # Check progress: tail -f ~/worktrees/name/ios_prebuild.log
   ```

4. **Monitor multiple worktrees**: Use tmux/screen
   ```bash
   tmux new-session -d -s work1 -c ~/worktrees/feature1 './start.sh'
   tmux new-session -d -s work2 -c ~/worktrees/feature2 './start.sh'
   ```

5. **Update from main**: Sync latest changes
   ```bash
   cd /path/to/worktree
   git fetch origin
   git rebase origin/main
   ```

## 🎓 Learn More

- Full guide: `WORKTREE_SETUP.md`
- Startup options: `./start.sh --help`
- Backend docs: `backend/README.md` or `docs/arch/backend.md`
- Frontend docs: `admin/README.md` or `docs/arch/frontend.md`
- Mobile docs: `mobile/README.md`

---

**Need help?** See `WORKTREE_SETUP.md` for detailed documentation and troubleshooting.