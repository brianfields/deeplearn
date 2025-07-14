# CLI Learning Path Creator

A Python command-line tool to create learning paths with rich bite-sized content that appears in the frontend interface.

## Installation

No installation required - the script uses built-in Python libraries and `requests` (should be available in your environment).

## Usage

### Basic Usage

```bash
# Simple topic creation
python create_learning_path.py "Introduction to Machine Learning"

# Or using the alias
./create-topic "Introduction to Machine Learning"
```

### Advanced Usage

```bash
# Specify skill level
python create_learning_path.py "Advanced Python" --level advanced

# Add refinements
python create_learning_path.py "Web Development" --refinements "Focus on React" "Include TypeScript"

# Custom instructions
python create_learning_path.py "Data Science" --instructions "Use real-world examples and datasets"

# Combine all options
python create_learning_path.py "Machine Learning" \
  --level intermediate \
  --refinements "Focus on practical applications" "Include Python code examples" \
  --instructions "Make it suitable for someone with basic programming experience"
```

### Command Line Options

- `topic` (required): The main topic for the learning path
- `--level`: User skill level (`beginner`, `intermediate`, `advanced`) - default: `beginner`
- `--refinements`: List of refinement suggestions (can specify multiple)
- `--instructions`: Custom instructions for content generation
- `--server`: API server URL (default: `http://localhost:8000`)
- `--json`: Output result as JSON

## Examples

### 1. Simple Creation
```bash
python create_learning_path.py "Introduction to Python"
```

**Output:**
```
🚀 Creating learning path for: Introduction to Python
📊 User level: beginner
⏳ Generating content... (this may take 5-10 minutes for rich content)
✅ Learning path created successfully!
🆔 Path ID: path_20250713_120748_abc123
📚 Topic: Introduction to Python
📝 Total topics: 6
🎯 Bite-sized content: 5 topics with complete strategy
🌐 View in frontend: http://localhost:3000/courses/path_20250713_120748_abc123
```

### 2. Advanced Creation with Refinements
```bash
python create_learning_path.py "React Development" \
  --level intermediate \
  --refinements "Focus on hooks" "Include testing" \
  --instructions "Use modern React patterns and best practices"
```

### 3. Using the Alias
```bash
./create-topic "Database Design" --level advanced
```

## Rich Content Generated

The tool creates learning paths with the **COMPLETE strategy**, generating 6 types of content per topic:

1. **Didactic Snippet** - Core teaching content
2. **Glossary** - Concept definitions and explanations
3. **Socratic Dialogues** - Interactive conversation-style learning
4. **Short Answer Questions** - Open-ended assessment questions
5. **Multiple Choice Questions** - Structured assessment options
6. **Post-Topic Quiz** - Comprehensive evaluation materials

## Example Generated Content

For a topic like "Introduction to CLI", the system generates:
- **21 components total** (vs 2-3 with old system)
- Multiple choice question sets (8 questions each)
- Short answer question sets (6 questions each)
- Post-topic quizzes (6-8 items each)
- Socratic dialogues (8 items)
- Rich glossary entries
- Comprehensive didactic content

## Viewing Results

### In the Frontend
The created learning path immediately appears in the web interface:
```
http://localhost:3000/courses/[path_id]
```

### Using Inspection Tools
```bash
# List all learning paths
./inspect all

# Show topics for specific path
./inspect topics-for-path [path_id]

# Show detailed content for a topic
./inspect topic [topic_uuid]

# Check system status
./check-strategy
```

## Error Handling

The script handles common issues:

- **Connection errors**: Suggests starting the backend server
- **Timeouts**: Informs that generation continues in background
- **API errors**: Shows detailed error messages
- **Invalid inputs**: Provides helpful usage guidance

## Requirements

- Backend server running on `http://localhost:8000` (or custom URL)
- Python 3.7+ with `requests` library
- Valid OpenAI API key configured in backend

## Performance Notes

- **Generation time**: 5-10 minutes for 5 topics with rich content
- **Timeout handling**: 10-minute timeout with background completion
- **Content quality**: Much richer than previous CORE_ONLY strategy
- **Frontend integration**: Immediate availability after generation

## Troubleshooting

### Backend Not Running
```
❌ Could not connect to server. Is the backend running?
💡 Start server with: python start_server.py
```

### Timeout Issues
```
⏰ Request timed out. Content generation is still running in background.
🔍 Check status with: ./inspect all
```

### Check Overall Status
```bash
./check-strategy  # Shows system overview
```