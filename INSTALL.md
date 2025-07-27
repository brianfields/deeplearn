# DeepLearn Installation Guide

This guide will help you set up the DeepLearn platform on macOS using our automated installation script.

## 🚀 Quick Installation

### Prerequisites

- **macOS** (tested on macOS 12+)
- **Homebrew** (for package management)
- **Git** (for cloning the repository)

### Automated Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd deeplearn
   ```

2. **Run the installation script:**
   ```bash
   ./install.sh
   ```

3. **Add your OpenAI API key:**
   ```bash
   # Edit the environment file
   nano backend/.env
   # Find this line: OPENAI_API_KEY=your_openai_api_key_here
   # Replace 'your_openai_api_key_here' with your actual API key
   # Example: OPENAI_API_KEY=sk-1234567890abcdef...
   ```

4. **Start the platform:**
   ```bash
   ./start.sh
   ```

## 🔧 What the Installation Script Does

The `install.sh` script automates the following steps:

### 1. Prerequisites Check
- ✅ Verifies Homebrew is installed
- ✅ Checks Python 3.11+ is available
- ✅ Ensures Node.js 18+ is installed
- ✅ Installs missing dependencies via Homebrew

### 2. Database Setup
- ✅ Installs PostgreSQL 14 via Homebrew
- ✅ Starts PostgreSQL service
- ✅ Creates `deeplearn` database
- ✅ Creates `deeplearn_user` database user
- ✅ Grants necessary permissions

### 3. Python Environment
- ✅ Creates Python virtual environment (`venv`)
- ✅ Upgrades pip to latest version
- ✅ Installs all Python dependencies from `backend/requirements.txt`

### 4. Backend Configuration
- ✅ Creates `.env` file with default configuration
- ✅ Runs Alembic database migrations
- ✅ Initializes database schema

### 5. Mobile App Setup
- ✅ Installs Node.js dependencies via npm
- ✅ Sets up Expo development environment

### 6. Convenience Scripts
- ✅ Creates `start.sh` script for easy startup
- ✅ Provides colored output and error handling

## 🎯 Manual Installation

If you prefer to install manually or need to troubleshoot, see the detailed steps in [QUICKSTART.md](QUICKSTART.md).

## 🆘 Troubleshooting

### Common Issues

**"Homebrew not found"**
```bash
# Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**"Permission denied"**
```bash
# Make the script executable
chmod +x install.sh
```

**"Python version too old"**
```bash
# The script will install Python 3.11, but you may need to restart your terminal
# Then run the script again
```

**"PostgreSQL connection failed"**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if needed
brew services start postgresql
```

**"OpenAI API key not set"**
```bash
# Edit the environment file
nano backend/.env
# Find this line: OPENAI_API_KEY=your_openai_api_key_here
# Replace 'your_openai_api_key_here' with your actual API key
# Example: OPENAI_API_KEY=sk-1234567890abcdef...
```

## 📱 After Installation

Once installation is complete:

1. **Add your OpenAI API key** to `backend/.env` (find the line `OPENAI_API_KEY=your_openai_api_key_here` and replace with your actual key)
2. **Start the platform** with `./start.sh`
3. **Access the API** at http://localhost:8000
4. **View API docs** at http://localhost:8000/docs
5. **Use the mobile app** via Expo development server

## 🔄 Updating

To update the platform:

```bash
# Pull latest changes
git pull

# Re-run installation script (it's safe to run multiple times)
./install.sh
```

## 🗑️ Uninstalling

To completely remove DeepLearn:

```bash
# Stop services
brew services stop postgresql

# Remove database
dropdb deeplearn
dropuser deeplearn_user

# Remove virtual environment
rm -rf venv

# Remove node modules
rm -rf mobile/node_modules

# Remove the entire project
cd ..
rm -rf deeplearn
```

## 📞 Support

If you encounter issues:

1. Check this installation guide
2. Review the main [QUICKSTART.md](QUICKSTART.md)
3. Check the [README.md](README.md) for project details
4. Ensure all prerequisites are met
5. Verify your OpenAI API key is valid

---

**Happy Learning! 🚀**
