#!/bin/bash

# Setup Git Worktree Script
# This script creates a new git worktree with a fresh branch and sets up all dependencies
# Usage: ./setup_worktree.sh <branch-name> [worktree-path]

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Utility functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    print_error "Missing required argument"
    echo "Usage: $0 <branch-name> [worktree-path] [--ios-prebuild]"
    echo ""
    echo "Examples:"
    echo "  $0 feature/awesome-feature"
    echo "  $0 bugfix/issue-123 ~/code/worktrees/issue-123"
    echo "  $0 feature/my-feature ~/worktrees/my-feature --ios-prebuild"
    exit 1
fi

BRANCH_NAME=$1
WORKTREE_PATH=${2:-./../${BRANCH_NAME#*/}}  # Default to ../branch-name if not specified
IOS_PREBUILD=0

# Parse optional flags
shift 2 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ios-prebuild)
            IOS_PREBUILD=1
            ;;
        *)
            print_warning "Unknown option: $1 (ignoring)"
            ;;
    esac
    shift
done

# Get the absolute path of the worktree
WORKTREE_PATH=$(cd "$(dirname "$WORKTREE_PATH")" && pwd)/$(basename "$WORKTREE_PATH")

# Get the directory where the current repo is
REPO_DIR="$(pwd)"

print_info "Setting up worktree with the following configuration:"
echo "  Branch: $BRANCH_NAME"
echo "  Worktree Path: $WORKTREE_PATH"
echo "  Current Repo: $REPO_DIR"
echo ""

# Check if worktree directory already exists
if [ -d "$WORKTREE_PATH" ]; then
    print_error "Worktree directory already exists at $WORKTREE_PATH"
    exit 1
fi

# Step 1: Create git worktree
print_info "Creating git worktree..."
if git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH"; then
    print_success "Git worktree created"
else
    print_error "Failed to create git worktree"
    exit 1
fi

# Navigate to the worktree
cd "$WORKTREE_PATH"
print_success "Navigated to worktree directory"

# Step 2: Set up backend Python venv
print_info "Setting up Python virtual environment..."
if python3 -m venv backend/venv; then
    print_success "Python virtual environment created"
else
    print_error "Failed to create Python virtual environment"
    cd "$REPO_DIR"
    git worktree remove "$WORKTREE_PATH"
    exit 1
fi

# Activate venv and install backend dependencies
print_info "Installing backend dependencies..."
if source backend/venv/bin/activate && pip install --upgrade pip setuptools wheel >/dev/null 2>&1; then
    print_success "pip upgraded"
else
    print_warning "Failed to upgrade pip (continuing anyway)"
fi

if pip install -r backend/requirements.txt >/dev/null 2>&1; then
    print_success "Backend dependencies installed"
else
    print_error "Failed to install backend dependencies"
    cd "$REPO_DIR"
    git worktree remove "$WORKTREE_PATH"
    exit 1
fi

# Step 3: Set up admin frontend
print_info "Installing admin dashboard dependencies..."
if cd admin && npm install >/dev/null 2>&1; then
    print_success "Admin dashboard dependencies installed"
    cd ..
else
    print_error "Failed to install admin dashboard dependencies"
    cd "$REPO_DIR"
    git worktree remove "$WORKTREE_PATH"
    exit 1
fi

# Step 4: Set up mobile app
print_info "Installing mobile app dependencies..."
if cd mobile && npm install >/dev/null 2>&1; then
    print_success "Mobile app dependencies installed"
    cd ..
else
    print_error "Failed to install mobile app dependencies"
    cd "$REPO_DIR"
    git worktree remove "$WORKTREE_PATH"
    exit 1
fi

# Step 5: Set up .env files
print_info "Setting up environment configuration..."

# Check if .env exists in main repo
if [ -f "$REPO_DIR/.env" ]; then
    # Copy .env from main repo to worktree root
    cp "$REPO_DIR/.env" "$WORKTREE_PATH/.env"
    print_success ".env copied from main repo"

    # Create symlink in backend directory pointing to root .env
    cd backend
    if ln -sf ../.env .env; then
        print_success ".env symlink created in backend/"
    else
        print_warning "Failed to create symlink (backend/.env may already exist)"
    fi
    cd ..
else
    # If no .env in main repo, try to copy from backend/.env
    if [ -f "$REPO_DIR/backend/.env" ]; then
        cp "$REPO_DIR/backend/.env" "$WORKTREE_PATH/.env"
        print_success ".env copied from backend (main repo)"

        cd backend
        if ln -sf ../.env .env; then
            print_success ".env symlink created in backend/"
        else
            print_warning "Failed to create symlink (backend/.env may already exist)"
        fi
        cd ..
    else
        # No .env found, try .env.example as fallback
        if [ -f "$REPO_DIR/backend/env.example" ]; then
            cp "$REPO_DIR/backend/env.example" "$WORKTREE_PATH/.env"
            print_warning ".env not found, using env.example as template"
            print_warning "You should edit .env with your actual configuration"

            cd backend
            if ln -sf ../.env .env; then
                print_success ".env symlink created in backend/"
            else
                print_warning "Failed to create symlink"
            fi
            cd ..
        else
            print_warning "No .env file found in main repo"
        fi
    fi
fi

# Step 6: Optional iOS prebuild (background)
IOS_BUILD_PID=""
IOS_BUILD_LOG=""
if [ $IOS_PREBUILD -eq 1 ]; then
    print_info "Starting iOS prebuild in background..."
    cd mobile
    IOS_BUILD_LOG="$WORKTREE_PATH/ios_prebuild.log"
    nohup npm run ios:prebuild > "$IOS_BUILD_LOG" 2>&1 &
    IOS_BUILD_PID=$!
    cd ..
    print_success "iOS prebuild started (PID: $IOS_BUILD_PID)"
fi

# Summary
echo ""
print_success "Worktree setup complete!"
echo ""
print_info "Your worktree is ready to use. To start working:"
echo ""
echo "  cd $WORKTREE_PATH"
echo "  ./start.sh"
echo ""
print_info "To run specific services:"
echo ""
echo "  # Backend only"
echo "  cd backend && source venv/bin/activate && python server.py"
echo ""
echo "  # Admin dashboard"
echo "  cd admin && npm run dev"
echo ""
echo "  # Mobile app"
echo "  cd mobile && npm start"
echo ""

# iOS prebuild status
if [ -n "$IOS_BUILD_PID" ]; then
    echo ""
    print_info "iOS Prebuild Status:"
    echo "  PID: $IOS_BUILD_PID"
    echo "  Log: tail -f $IOS_BUILD_LOG"
    echo ""
    echo "  To check if prebuild is complete:"
    echo "    kill -0 $IOS_BUILD_PID && echo 'Still running' || echo 'Complete'"
    echo ""
    print_info "When ready, the native iOS project will be built at:"
    echo "  $WORKTREE_PATH/mobile/ios/"
    echo ""
fi

print_info "To remove the worktree when done:"
echo ""
echo "  cd $REPO_DIR"
echo "  git worktree remove $WORKTREE_PATH"
echo ""
