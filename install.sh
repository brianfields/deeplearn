#!/bin/bash

# DeepLearn Installation Script for macOS
# This script automates the complete setup of the DeepLearn platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Homebrew is installed
check_homebrew() {
    if ! command_exists brew; then
        # Try to find Homebrew in common locations
        if [ -f "/opt/homebrew/bin/brew" ]; then
            export PATH="/opt/homebrew/bin:$PATH"
            print_success "Found Homebrew in /opt/homebrew/bin, added to PATH"
        elif [ -f "/usr/local/bin/brew" ]; then
            export PATH="/usr/local/bin:$PATH"
            print_success "Found Homebrew in /usr/local/bin, added to PATH"
        else
            print_error "Homebrew is not installed. Please install it first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    fi
    print_success "Homebrew is installed"
}

# Function to check and install Python
check_python() {
    if ! command_exists python3; then
        print_warning "Python 3 is not installed. Installing via Homebrew..."
        brew install python@3.13
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    if [[ "$PYTHON_VERSION" < "3.10" ]]; then
        print_error "Python 3.10+ is required. Current version: $PYTHON_VERSION"
        print_warning "Installing Python 3.13 via Homebrew..."
        brew install python@3.13
        print_warning "Please restart your terminal and run this script again"
        exit 1
    fi
    print_success "Python $(python3 --version) is installed"
}

# Function to check and install Node.js
check_nodejs() {
    if ! command_exists node; then
        print_warning "Node.js is not installed. Installing via Homebrew..."
        brew install node@18
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d. -f1)
    if [[ "$NODE_VERSION" < "18" ]]; then
        print_error "Node.js 18+ is required. Current version: $(node --version)"
        print_warning "Installing Node.js 18 via Homebrew..."
        brew install node@18
        print_warning "Please restart your terminal and run this script again"
        exit 1
    fi
    print_success "Node.js $(node --version) is installed"
}

# Function to check and install PostgreSQL
check_postgresql() {
    if ! command_exists psql; then
        print_warning "PostgreSQL is not installed. Installing via Homebrew..."
        brew install postgresql@14
        brew services start postgresql@14
    else
        # Check if PostgreSQL service is running
        if ! brew services list | grep -q "postgresql.*started"; then
            print_warning "PostgreSQL service is not running. Starting it..."
            brew services start postgresql
        fi
    fi
    print_success "PostgreSQL is installed and running"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."

    # Create database if it doesn't exist
    if ! psql -lqt | cut -d \| -f 1 | grep -qw deeplearn; then
        print_status "Creating database 'deeplearn'..."
        createdb deeplearn
    else
        print_success "Database 'deeplearn' already exists"
    fi

    # Create user if it doesn't exist (connect to postgres database which always exists)
    if ! psql -d postgres -t -c "SELECT 1 FROM pg_roles WHERE rolname='deeplearn_user'" | grep -q 1; then
        print_status "Creating user 'deeplearn_user'..."
        createuser --interactive deeplearn_user --no-password
    else
        print_success "User 'deeplearn_user' already exists"
    fi

    # Grant permissions (these commands are safe to run multiple times)
    print_status "Setting up database permissions..."
    psql -d deeplearn -c "GRANT ALL PRIVILEGES ON DATABASE deeplearn TO deeplearn_user;" 2>/dev/null || true
    psql -d deeplearn -c "GRANT ALL ON SCHEMA public TO deeplearn_user;" 2>/dev/null || true

    print_success "Database setup complete"
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."

    if [ ! -d "deeplearn" ]; then
        python3 -m venv deeplearn
        print_success "Python virtual environment created"
    else
        print_success "Python virtual environment already exists"
    fi

    source deeplearn/bin/activate

    # Upgrade pip (safe to run multiple times)
    print_status "Upgrading pip..."
    pip install --upgrade pip

    print_success "Python virtual environment ready"
}

# Function to install backend dependencies
install_backend_deps() {
    print_status "Installing backend dependencies..."

    # Install Python dependencies (pip will skip already installed packages)
    pip install -r backend/requirements.txt

    print_success "Backend dependencies installed"
}

# Function to setup environment file
setup_env_file() {
    print_status "Setting up environment configuration..."

    # Check if .env file exists
    if [ ! -f "backend/.env" ]; then
        print_warning "Creating .env file. You'll need to add your OpenAI API key."

        # Prompt user for OpenAI API key
        echo
        echo -e "${YELLOW}🔑 OpenAI API Key Required${NC}"
        echo "To use DeepLearn, you need an OpenAI API key."
        echo "Get one at: https://platform.openai.com/api-keys"
        echo
        read -p "Enter your OpenAI API key (or press Enter to skip for now): " openai_key

        if [ -n "$openai_key" ]; then
            print_success "API key provided, creating .env file..."
        else
            print_warning "No API key provided. You'll need to add it later to backend/.env"
            openai_key="your_openai_api_key_here"
        fi

        cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://deeplearn_user@localhost:5432/deeplearn
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=deeplearn
DATABASE_USER=deeplearn_user
DATABASE_PASSWORD=

# OpenAI Configuration (Required)
OPENAI_API_KEY=$openai_key

# Optional Configuration
OPENAI_MODEL=gpt-4o
USER_LEVEL=beginner
LESSON_DURATION=15
MASTERY_THRESHOLD=0.9
TEMPERATURE=0.7
MAX_TOKENS=1500
CACHE_ENABLED=true
DEBUG=false
EOF

        if [ "$openai_key" = "your_openai_api_key_here" ]; then
            print_warning "⚠️  IMPORTANT: You need to edit backend/.env and replace 'your_openai_api_key_here' with your actual OpenAI API key"
        else
            print_success "OpenAI API key configured successfully"
        fi
    else
        print_success ".env file already exists"
        print_warning "If you need to update your OpenAI API key, edit backend/.env"
    fi
}

# Function to initialize database schema
init_database() {
    print_status "Initializing database schema..."

    # Run Alembic migrations (safe to run multiple times)
    cd backend
    alembic upgrade head
    cd ..

    print_success "Database schema initialized"
}

# Function to install mobile dependencies
install_mobile_deps() {
    print_status "Installing mobile app dependencies..."

    # Install Node.js dependencies (npm will skip already installed packages)
    cd mobile
    npm install
    cd ..

    print_success "Mobile app dependencies installed"
}

# Function to create start script
create_start_script() {
    print_status "Creating start script..."

    cat > start.sh << 'EOF'
#!/bin/bash

# DeepLearn Start Script
# This script starts both the backend and mobile apps

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting DeepLearn Platform...${NC}"

# Function to cleanup background processes on exit
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    kill $BACKEND_PID $MOBILE_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
source ../deeplearn/bin/activate
python start_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start mobile app
echo -e "${GREEN}Starting mobile app...${NC}"
cd ../mobile
npm start &
MOBILE_PID=$!

echo -e "${GREEN}DeepLearn Platform is starting up!${NC}"
echo -e "${BLUE}Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}Mobile app: Expo development server starting...${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for background processes
wait
EOF

    chmod +x start.sh
    print_success "Start script created: ./start.sh"
}

# Function to display final instructions
show_final_instructions() {
    echo
    echo -e "${GREEN}🎉 DeepLearn installation complete!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. If you haven't added your OpenAI API key yet:"
    echo "   - Edit the file: backend/.env"
    echo "   - Find the line: OPENAI_API_KEY=your_openai_api_key_here"
    echo "   - Replace 'your_openai_api_key_here' with your actual API key"
    echo "   - Get an API key at: https://platform.openai.com/api-keys"
    echo
    echo "2. Run './start.sh' to start both backend and mobile apps"
    echo "3. Open http://localhost:8000/docs to view API documentation"
    echo "4. Use the mobile app or API to start learning!"
    echo
    echo -e "${YELLOW}Note:${NC} The app won't work without a valid OpenAI API key"
    echo
}

# Main installation function
main() {
    echo -e "${BLUE}🚀 DeepLearn Installation Script for macOS${NC}"
    echo "=================================================="
    echo

    # Check prerequisites
    print_status "Checking prerequisites..."
    check_homebrew
    check_python
    check_nodejs
    check_postgresql

    # Setup database
    setup_database

    # Setup Python environment
    setup_python_env

    # Install dependencies
    install_backend_deps
    setup_env_file
    init_database

    # Install mobile dependencies
    install_mobile_deps

    # Create start script
    create_start_script

    # Show final instructions
    show_final_instructions
}

# Run main function
main "$@"
