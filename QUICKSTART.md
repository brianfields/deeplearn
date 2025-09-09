# Quick Start Guide

Get up and running with the Conversational Learning App in minutes!

Experience ChatGPT-like learning with a Socratic AI tutor that adapts to your responses in real-time.

## 🚀 Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get an OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Keep it handy for configuration

3. **Set up environment variables:**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env file with your API key
   # OPENAI_API_KEY=your-api-key-here
   ```

4. **Run the conversational learning app:**
   ```bash
   python learn.py
   ```

   Or use the original interface:
   ```bash
   python main.py
   ```

## 📋 First-Time Setup

When you first run the app:

1. **Environment variables are loaded automatically** from your .env file
2. **Optional: Adjust settings** in the app if needed
   - Go to Settings (option 5) to view current configuration
   - Most settings are now configured via environment variables

## 🔧 Configuration Options

### Environment Variables (.env file)

The app supports extensive configuration via environment variables:

```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Optional (with defaults)
OPENAI_MODEL=gpt-5
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

### Starting a New Learning Path

1. Select "Start New Learning Path" from the main menu
2. Enter a topic (e.g., "Python Programming", "Project Management")
3. Choose your current level
4. Add any specific focus areas (optional)
5. Review and confirm the generated syllabus
6. Start learning!

### Learning Flow

The app follows a structured learning flow:

1. **Lesson** - Interactive AI-generated content
2. **Quiz** - Test your understanding
3. **Progress** - Track your mastery
4. **Next Topic** - Advance when ready

### Example Conversational Learning Session

```
💬 Conversational Learning App
===============================

1. Start New Learning Topic
2. Continue Learning
3. View Learning Progress
4. Settings
5. Exit

Select option: 1

What would you like to learn about?: Python Programming

Creating your personalized learning path...
✅ Created learning path: Python Programming Fundamentals

Learning Topics:
#  Topic                        Objectives
1  Variables and Data Types     Understand variables, Know basic data types...
2  Control Flow                 Use if statements, Write loops...
3  Functions                    Define functions, Use parameters...

Start with the first topic? (y/n): y

🤖 AI Tutor: Hey there! I'm excited to explore Variables and Data Types with you today.

Instead of diving straight into definitions, let me ask you this: What comes to mind when you think about variables and data types? Have you encountered this concept before, maybe in your work or daily life?

I'm curious about your perspective before we start our journey together! 🤔

You: I think variables are like containers that hold information?

🤖 AI Tutor: Exactly! That's a great way to think about it. Variables are indeed like containers or boxes that hold information.

Since you mentioned containers, let me ask you this: when you organize things at home, do you use different types of containers for different things? Like maybe a glass jar for cookies and a plastic bag for vegetables?

I'm wondering if you can see a connection between that and how we might handle different types of information in programming...

📊 Progress: Understanding 20%, Engagement 85%
   Concepts: 0 mastered, 1 covered
```

## 🔧 Settings

### Available Settings

- **User Level**: beginner, intermediate, advanced
- **OpenAI API Key**: Your OpenAI API key
- **OpenAI Model**: gpt-5-nano, gpt-5-mini, gpt-5
- **Lesson Duration**: Default 15 minutes

### Cost Optimization

- **gpt-5-nano**: Most cost-effective option
- **gpt-5-mini**: Higher quality but more expensive
- **gpt-5-large**: Highest quality but most expensive

## 📊 Progress Tracking

### View Your Progress

Select "View Progress" from the main menu to see:
- All learning paths
- Completion status
- Last accessed dates

### Continue Learning

Select "Continue Existing Path" to:
- Resume where you left off
- See recommended next actions
- Continue your learning journey

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

From "Manage Learning Paths":
- **List**: View all paths
- **Delete**: Remove unwanted paths
- **Reset**: Start over with a path

## 🆘 Troubleshooting

### Common Issues

**"Learning service not available"**
- Check your OpenAI API key in settings
- Verify your internet connection
- Ensure you have API credits

**"Error generating content"**
- Check your OpenAI API key
- Try a different model (gpt-3.5-turbo is more reliable)
- Check OpenAI service status

**Slow responses**
- GPT-4 is slower than GPT-3.5-turbo
- Check your internet connection
- Try during off-peak hours

### Data Location

Your learning data is stored in:
```
.learning_data/
├── learning_paths.json    # Your learning paths
├── current_session.json   # Current session data
└── settings.json         # App settings
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

## 🤝 Getting Help

If you encounter issues:

1. Check this quick start guide
2. Review the main README.md
3. Check your OpenAI API key and credits
4. Try different models or settings

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

**Ready to start learning?** Run `python main.py` and begin your AI-powered learning journey! 🚀