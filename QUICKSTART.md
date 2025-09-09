# Quick Start Guide

Get up and running with the DeepLearn AI-Powered Learning Platform on macOS in minutes!

Experience ChatGPT-like learning with a Socratic AI tutor that adapts to your responses in real-time, featuring a FastAPI backend and React Native mobile app.

## 🚀 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.13+ and pip
- **Node.js** 18+ and npm
- **PostgreSQL** 12+
- **OpenAI API Key** (for content generation)

## 🏗️ Installation

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd deeplearn

# Run the automated installation script
./install.sh
```

The script will:
- Install all dependencies
- Set up PostgreSQL
- Create the database
- Configure environment variables
- Start both backend and mobile apps

### Option 2: Manual Installation

#### 1. Clone and Setup Project

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd deeplearn

# Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate
```

#### 2. Database Setup

**Install PostgreSQL:**
```bash
brew install postgresql
brew services start postgresql
```

**Create Database:**
```bash
# Create database and user
createdb deeplearn
createuser --interactive deeplearn_user

# Grant permissions
psql -d deeplearn -c "GRANT ALL PRIVILEGES ON DATABASE deeplearn TO deeplearn_user;"
```

#### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://deeplearn_user:your_password@localhost:5432/deeplearn
# OR use individual components:
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=deeplearn
# DATABASE_USER=deeplearn_user
# DATABASE_PASSWORD=your_password

# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

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

# Initialize database schema
alembic upgrade head
```

#### 4. Mobile App Setup

```bash
# Navigate to mobile directory
cd ../mobile

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

## 🚀 Running the Application

### Start the Backend Server

```bash
# From the backend directory
cd backend
python start_server.py
```

The server will be available at:
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API Docs**: http://localhost:8000/redoc

### Start the Mobile App

```bash
# From the mobile directory
cd mobile
npm start
```

This will start the Expo development server. You can:
- Press `i` to open iOS simulator
- Press `a` to open Android emulator
- Scan the QR code with Expo Go app on your phone

## 📋 First-Time Setup

When you first run the app:

1. **Environment variables are loaded automatically** from your .env file
2. **Database schema is initialized** with Alembic migrations
3. **API server starts** and is ready to accept requests
4. **Mobile app connects** to the backend API

## 🔧 Configuration Options

### Environment Variables (.env file)

The app supports extensive configuration via environment variables:

```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Database (choose one method)
DATABASE_URL=postgresql://username:password@localhost:5432/deeplearn
# OR individual components:
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=deeplearn
# DATABASE_USER=username
# DATABASE_PASSWORD=password

# Optional (with defaults)
OPENAI_MODEL=gpt-4o
USER_LEVEL=beginner
LESSON_DURATION=15
MASTERY_THRESHOLD=0.9
TEMPERATURE=0.7
CACHE_ENABLED=true
DEBUG=false
```

### Azure OpenAI Support

For Azure OpenAI, use these variables instead:

```bash
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15
```

## 🎯 Using the App

### API Endpoints

The backend provides REST API endpoints for:

- **Learning Paths**: Create and manage learning topics
- **Content Creation**: Generate educational content
- **Progress Tracking**: Monitor learning progress
- **Real-time Chat**: WebSocket connections for interactive learning

### Mobile App Features

- **Topic Selection**: Choose from available learning topics
- **Interactive Learning**: Engage with AI-generated content
- **Progress Tracking**: View your learning progress
- **Quiz System**: Test your understanding with MCQs

### Example API Usage

```bash
# Create a new learning topic
curl -X POST "http://localhost:8000/api/learning/topics" \
  -H "Content-Type: application/json" \
  -d '{"title": "Python Programming", "level": "beginner"}'

# Get available topics
curl "http://localhost:8000/api/learning/topics"
```

## 🔧 Settings

### Available Settings

- **User Level**: beginner, intermediate, advanced
- **OpenAI API Key**: Your OpenAI API key
- **OpenAI Model**: gpt-3.5-turbo, gpt-4o
- **Lesson Duration**: Default 15 minutes

### Cost Optimization

- **gpt-3.5-turbo**: Most cost-effective option
- **gpt-4o**: Higher quality but more expensive

## 📊 Progress Tracking

### View Your Progress

The API provides endpoints to track:
- All learning paths
- Completion status
- Last accessed dates
- Quiz results

### Continue Learning

Resume where you left off by:
- Selecting existing topics
- Continuing from last session
- Reviewing completed content

## 🎓 Learning Tips

### For Best Results

1. **Complete lessons thoroughly** - Take time to understand concepts
2. **Take quizzes seriously** - They help reinforce learning
3. **Review regularly** - The app tracks your progress over time
4. **Be specific with topics** - "Python web development" vs "Python"

### Topic Ideas

**Programming:**
- Python for Data Science
- JavaScript Web Development
- SQL Database Management

**Business:**
- Project Management Fundamentals
- Digital Marketing Strategies
- Leadership and Team Building

**Other:**
- Machine Learning Basics
- Cloud Computing with AWS
- UX/UI Design Principles

## 🔍 Managing Learning Paths

### Multiple Paths

You can have multiple learning paths:
- Switch between different topics
- Track progress independently
- Continue from where you left off

### Path Management

Use the API endpoints to:
- **List**: View all paths
- **Delete**: Remove unwanted paths
- **Reset**: Start over with a path

## 🆘 Troubleshooting

### Common Issues

**"Database connection failed"**
- Check PostgreSQL is running: `brew services list | grep postgresql`
- Verify database credentials in .env
- Ensure database exists and user has permissions

**"Learning service not available"**
- Check your OpenAI API key in .env
- Verify your internet connection
- Ensure you have API credits

**"Error generating content"**
- Check your OpenAI API key
- Try a different model (gpt-3.5-turbo is more reliable)
- Check OpenAI service status

**"Mobile app can't connect to backend"**
- Ensure backend server is running on port 8000
- Check CORS settings in backend
- Verify network connectivity

**Slow responses**
- GPT-4 is slower than GPT-3.5-turbo
- Check your internet connection
- Try during off-peak hours

### Data Location

Your learning data is stored in:
```
backend/
├── .learning_data/          # Learning data (if using file storage)
└── database/                # PostgreSQL database

mobile/
└── .expo/                   # Expo development data
```

## 🎯 Next Steps

### After Getting Started

1. **Complete your first learning path** to understand the flow
2. **Experiment with different topics** to find what interests you
3. **Adjust settings** to match your learning style
4. **Use the progress tracking** to stay motivated

### Advanced Usage

- Try different user levels for the same topic
- Use specific refinements to focus on particular areas
- Manage multiple learning paths for different skills
- Review completed topics periodically
- Explore the API documentation at http://localhost:8000/docs

## 🤝 Getting Help

If you encounter issues:

1. Check this quick start guide
2. Review the main README.md
3. Check your OpenAI API key and credits
4. Try different models or settings
5. View API documentation at http://localhost:8000/docs

## 📈 Learning Efficiency

### Maximize Your Learning

- **Set realistic goals** - Start with beginner level
- **Be consistent** - Regular short sessions work better
- **Take notes** - The app complements but doesn't replace notes
- **Practice outside the app** - Apply what you learn

### Track Your Progress

- Use the progress view regularly
- Celebrate completed topics
- Review challenging areas
- Set learning goals

---

**Ready to start learning?** Start the backend server with `python start_server.py` and the mobile app with `npm start` to begin your AI-powered learning journey! 🚀
