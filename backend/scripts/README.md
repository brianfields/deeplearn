# Backend Scripts

This directory contains command-line scripts for various development and data management tasks.

## 📋 Available Scripts

### 🌱 `create_seed_data.py` - Seed Data Generation

Creates realistic seed data for development and testing without making actual LLM calls. Generates:
- Complete lesson with metadata
- 1 didactic snippet component
- 1 glossary component
- 5 multiple choice questions
- 1 FlowRun record
- 8 FlowStepRun records (1 metadata + 1 didactic + 1 glossary + 5 MCQs)
- 8 LLMRequest records with realistic token counts and costs

### 📚 `create_lesson.py` - Real Lesson Creation

Creates complete lessons using actual LLM API calls through the content creator service.

### 🎯 `create_mcqs.py` - MCQ Generation (Legacy)

The original MCQ creation script using a sophisticated two-pass approach:

1. **Pass 1**: Extract refined material from source text
2. **Pass 2**: Create individual MCQs for each topic/learning objective
3. **Pass 3**: Evaluate MCQ quality using best practices

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Database connection (PostgreSQL or SQLite)
- For real lesson creation: OpenAI API key
- Required dependencies (see `requirements.txt`)

### Seed Data Creation

```bash
# Create seed data with default lesson
python scripts/create_seed_data.py --verbose

# Create custom seed data
python scripts/create_seed_data.py \
    --lesson "Neural Networks Basics" \
    --concept "Backpropagation Algorithm" \
    --level "beginner" \
    --domain "Deep Learning" \
    --verbose \
    --output seed_summary.json
```

### Real Lesson Creation

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Create lesson from source material
python scripts/create_lesson.py \
    --lesson "PyTorch Cross-Entropy Loss" \
    --concept "Cross-Entropy Loss Function" \
    --material scripts/examples/cross_entropy_material.txt \
    --verbose
```

## 📖 Script Details

### 🌱 Seed Data Script (`create_seed_data.py`)

Creates realistic development data without API calls.

**Command Line Arguments:**

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--lesson` | No | Lesson title | "Cross-Entropy Loss in Deep Learning" |
| `--concept` | No | Core concept | "Cross-Entropy Loss Function" |
| `--level` | No | User level (beginner/intermediate/advanced) | `intermediate` |
| `--domain` | No | Subject domain | "Machine Learning" |
| `--verbose` | No | Show detailed progress | - |
| `--output` | No | Save summary to JSON file | - |

**Generated Data:**
- 1 lesson with 5 learning objectives and key concepts
- 1 didactic snippet with explanation and key points
- 1 glossary with 5 key terms and definitions
- 5 multiple choice questions (one per learning objective)
- 1 flow run record with realistic metrics (15,420 tokens, $0.0771 cost)
- 8 flow step run records (metadata extraction + component generation)
- 8 LLM request records with realistic request/response data

**Example Output:**
```
✅ Seed data created successfully!
   • Lesson ID: d9bdcecc-0eea-489b-9fea-fc5d700524c7
   • Title: Cross-Entropy Loss in Deep Learning
   • Components: 7 (1 didactic, 1 glossary, 5 MCQs)
   • Flow runs: 1
   • Step runs: 8
   • LLM requests: 8
   • Total tokens: 15420
   • Total cost: $0.0771
   • Frontend URL: http://localhost:3000/learn/d9bdcecc-0eea-489b-9fea-fc5d700524c7?mode=learning
```

### 📚 Real Lesson Creation (`create_lesson.py`)

Creates lessons using actual LLM API calls.

**Command Line Arguments:**

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--lesson` | Yes | Lesson title | - |
| `--concept` | Yes | Core concept to focus on | - |
| `--material` | Yes | Path to source material text file | - |
| `--level` | No | Target user level | `intermediate` |
| `--domain` | No | Subject domain | "Machine Learning" |
| `--verbose` | No | Show detailed progress | - |
| `--debug` | No | Enable debug logging | - |
| `--output` | No | Save content summary to JSON file | - |

## 🛠️ Development & Testing

### Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database (for seed data)
export DATABASE_URL="postgresql://user:pass@localhost:5432/deeplearn"
# OR for testing with SQLite
export DATABASE_URL="sqlite:///test.db"

# Create database tables
alembic upgrade head
```

### Testing Scripts

```bash
# Test seed data creation
python scripts/create_seed_data.py --verbose --output /tmp/test_summary.json

# Test real lesson creation (requires API key)
export OPENAI_API_KEY="your-key-here"
python scripts/create_lesson.py \
    --lesson "Test Lesson" \
    --concept "Test Concept" \
    --material scripts/examples/cross_entropy_material.txt \
    --verbose
```

## 🎯 Use Cases

### Development & Testing
- **Seed Data**: Create realistic test data without API costs
- **Database Testing**: Populate database with complete lesson structures
- **Frontend Development**: Test UI components with realistic data
- **Performance Testing**: Generate multiple lessons for load testing

### Production Setup
- **Content Creation**: Generate real lessons from source materials
- **Batch Processing**: Create multiple lessons from a content library
- **Quality Assurance**: Review generated content before publishing

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure DATABASE_URL is set correctly
   - For PostgreSQL: Check server is running and accessible
   - For SQLite: Ensure directory is writable

2. **"OpenAI API key not set"** (for real lesson creation)
   - Set the environment variable: `export OPENAI_API_KEY="your-key"`
   - Seed data script doesn't require API key

3. **Import Errors**
   - Make sure you're running from the backend directory
   - Check that all dependencies are installed: `pip install -r requirements.txt`

4. **Database Schema Issues**
   - Run migrations: `alembic upgrade head`
   - Check that all required tables exist

### Testing Without API Costs

The seed data script is perfect for development and testing:

```bash
# Create test data without any API calls
python scripts/create_seed_data.py --verbose

# Test with different parameters
python scripts/create_seed_data.py \
    --lesson "Custom Test Lesson" \
    --concept "Test Concept" \
    --level "beginner" \
    --verbose
```

## 📚 Related Documentation

- [Backend Architecture](../../docs/arch/backend.md)
- [Content Creator Module](../modules/content_creator/)
- [Flow Engine](../modules/flow_engine/)
- [Database Models](../modules/content/models.py)