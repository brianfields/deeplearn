# MCQ Creation Script

This directory contains a command-line script for creating Multiple Choice Questions (MCQs) from unstructured reference material using AI.

## 📋 Overview

The `create_mcqs.py` script uses a sophisticated two-pass approach to generate high-quality MCQs:

1. **Pass 1**: Extract refined material from source text
2. **Pass 2**: Create individual MCQs for each topic/learning objective
3. **Pass 3**: Evaluate MCQ quality using best practices

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key (set as environment variable)
- Required dependencies (see `requirements.txt`)

### Basic Usage

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Create MCQs from material
python scripts/create_mcqs.py --topic "Your Topic" --file your_material.txt
```

### Example: PyTorch Tensor Usage

A complete example with reference material is provided:

```bash
# Create MCQs about PyTorch tensor usage
python scripts/create_mcqs.py \
    --topic "PyTorch Tensor Usage" \
    --file pytorch_tensor_material.txt \
    --output pytorch_mcqs.json \
    --domain "Machine Learning" \
    --level intermediate \
    --verbose
```

## 📖 Command Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--topic` | Yes | Topic title for the MCQs | - |
| `--file` | Yes | Path to text file containing source material | - |
| `--output` | No | Output JSON file path | `mcqs_output.json` |
| `--domain` | No | Subject domain (e.g., "Machine Learning") | - |
| `--level` | No | Target user level | `intermediate` |
| `--model` | No | LLM model to use | `gpt-4` |
| `--verbose` | No | Show detailed progress and results | - |

## 📁 Input Material Format

The script accepts plain text files with your reference material. The material should be:
- Well-structured with clear topics and concepts
- Comprehensive enough to generate meaningful MCQs
- Written in a clear, educational style

### Example Material Structure

```
Topic Title: Your Main Topic

## Subtopic 1
Explanation of concepts, definitions, examples...

## Subtopic 2 
More detailed information, code examples if applicable...

## Key Concepts
- Important point 1
- Important point 2
- Important point 3

## Best Practices
Guidelines, tips, common mistakes to avoid...
```

## 📊 Output Format

The script generates a JSON file with the following structure:

```json
{
  "topic": "Topic Title",
  "domain": "Subject Domain",
  "user_level": "intermediate",
  "source_material_length": 3751,
  "refined_material": {
    "topics": [
      {
        "topic": "Subtopic Name",
        "learning_objectives": ["Objective 1", "Objective 2"],
        "key_facts": ["Fact 1", "Fact 2"],
        "common_misconceptions": [
          {
            "misconception": "Wrong belief",
            "correct_concept": "Correct understanding"
          }
        ],
        "assessment_angles": ["Angle 1", "Angle 2"]
      }
    ]
  },
  "mcqs": [
    {
      "mcq": {
        "stem": "Question text?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "rationale": "Explanation of why this is correct"
      },
      "evaluation": {
        "alignment": "Assessment of alignment with learning objectives",
        "stem_quality": "Quality of question stem",
        "options_quality": "Quality of answer options",
        "cognitive_challenge": "Appropriate cognitive level",
        "clarity_fairness": "Clarity and fairness assessment",
        "overall": "Overall quality summary"
      },
      "topic": "Associated topic",
      "learning_objective": "Target learning objective"
    }
  ],
  "summary": {
    "total_topics": 3,
    "total_mcqs": 8,
    "topics_covered": ["Topic 1", "Topic 2", "Topic 3"]
  }
}
```

## 🎯 Features

- **Two-pass AI approach** for higher quality MCQs
- **Automatic topic extraction** from unstructured material
- **Learning objective alignment** following Bloom's taxonomy
- **MCQ quality evaluation** using educational best practices
- **Detailed progress tracking** with verbose mode
- **Flexible output options** with JSON format
- **Error handling** with helpful error messages

## 🔍 Example Output

When you run the script with verbose mode, you'll see progress like:

```
Creating MCQs for topic: PyTorch Tensor Usage
Source material length: 3,751 characters
Target level: intermediate
Domain: Machine Learning

🔍 Starting two-pass MCQ creation...
📝 Pass 1: Extracting refined material from source text...
✅ Pass 1 completed: Found 4 topics
🧪 Pass 2: Created 12 MCQs
📊 Pass 3: Quality evaluation completed

🎉 Success! Created 12 MCQs
📚 Refined material extracted for 4 topics
💾 Results saved to: pytorch_mcqs.json

📋 Topics covered:
  - Creating Tensors (3 learning objectives)
  - Tensor Properties (2 learning objectives)
  - Basic Operations (4 learning objectives)
  - GPU Acceleration (3 learning objectives)

🎯 MCQ Quality Summary:
  MCQ 1: High quality MCQ following best practices for tensor creation
  MCQ 2: Well-constructed question testing tensor properties understanding
  ...

📊 Summary Statistics:
  - Total characters processed: 3,751
  - Topics identified: 4
  - MCQs created: 12
  - Target level: intermediate
  - Domain: Machine Learning

🔍 To view detailed results, check: pytorch_mcqs.json
```

## 🛠️ Troubleshooting

### Common Issues

1. **"OpenAI API key not set"**
   - Set the environment variable: `export OPENAI_API_KEY="your-key"`
   - Or the script will use a dummy key for testing

2. **"Input file not found"**
   - Check the file path is correct
   - Ensure the file exists and is readable

3. **"Input file is empty"**
   - Make sure your material file has content
   - Check file encoding (should be UTF-8)

4. **Import errors**
   - Make sure you're running from the backend directory
   - Check that all dependencies are installed

### Testing

To test the script without using API credits:

```bash
# Test script validation
python test_mcq_script.py

# Test with dummy API key
OPENAI_API_KEY="dummy_key" python scripts/create_mcqs.py --topic "Test" --file pytorch_tensor_material.txt
```

## 🔧 Development

The script uses the following internal components:
- `MCQService` - Core MCQ creation logic
- `PromptContext` - Context management for AI prompts
- `LLMClient` - Interface to language models

For development and testing, see the test files in the `tests/` directory:
- `test_mcq_service.py`
- `test_mcq_script.py`
- `test_mcq_prompts.py`

## 📚 Further Reading

- [MCQ Best Practices](../src/modules/lesson_planning/bite_sized_topics/prompts/CREATING_MCQs.md)
- [Bloom's Taxonomy Guide](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy)
- [Educational Assessment Principles](https://en.wikipedia.org/wiki/Educational_assessment)