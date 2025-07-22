# Topic Creation Guide

## 🚀 **Quick Start: Create a Complete Learning Topic**

Use this script to create a complete learning topic with didactic snippet and MCQs from source material.

### **1. Basic Usage**

```bash
cd backend

# Create a topic with default objectives
python scripts/create_topic_simple.py \
    --topic "PyTorch Cross-Entropy Loss" \
    --material scripts/examples/cross_entropy_material.txt \
    --verbose
```

### **2. With Custom Learning Objectives**

```bash
python scripts/create_topic_simple.py \
    --topic "PyTorch Cross-Entropy Loss" \
    --material scripts/examples/cross_entropy_material.txt \
    --objectives \
        "Understand cross-entropy calculation formula" \
        "Apply cross-entropy to classification problems" \
        "Identify valid tensor shapes for cross-entropy" \
        "Explain the purpose of reduction parameters" \
    --level intermediate \
    --domain "Machine Learning" \
    --verbose
```

### **3. Save Output to JSON File**

```bash
python scripts/create_topic_simple.py \
    --topic "PyTorch Cross-Entropy Loss" \
    --material scripts/examples/cross_entropy_material.txt \
    --output my_topic_output.json \
    --verbose
```

## 📋 **Script Parameters**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--topic` | ✅ | Topic title | "PyTorch Cross-Entropy Loss" |
| `--material` | ✅ | Path to source material file | `scripts/examples/cross_entropy_material.txt` |
| `--objectives` | ❌ | Learning objectives (space-separated) | "Understand X" "Apply Y" |
| `--level` | ❌ | User level (default: intermediate) | beginner/intermediate/advanced |
| `--domain` | ❌ | Subject domain (default: Machine Learning) | "Deep Learning" |
| `--verbose` | ❌ | Show detailed progress | |
| `--output` | ❌ | JSON output file path | `my_topic.json` |

## 🎯 **What Gets Created**

The script creates:

1. **Topic Record**: Main topic with metadata, objectives, and source material
2. **Didactic Snippet**: Educational content explaining the concept
3. **MCQ Components**: One multiple-choice question per learning objective
4. **Database Storage**: Everything saved to the PostgreSQL database

## 📂 **Generated Structure**

```
Topic: "PyTorch Cross-Entropy Loss"
├── Didactic Snippet: "Learn: PyTorch Cross-Entropy Loss"
├── MCQ 1: "Understand cross-entropy calculation formula"
├── MCQ 2: "Apply cross-entropy to classification problems"
├── MCQ 3: "Identify valid tensor shapes for cross-entropy"
└── MCQ 4: "Explain the purpose of reduction parameters"
```

## 🌐 **Accessing Your Topic**

After creation, you'll get:

```
🎉 Topic created successfully!
   • Topic ID: abc123...
   • Components: 1 didactic snippet + 4 MCQs
   • Frontend URL: http://localhost:3000/learn/abc123...?mode=learning
```

**Visit the Frontend URL** to see your topic in the learning interface!

## 📝 **Sample Material File Format**

Create a `.txt` file with comprehensive content about your topic:

```
Your Topic Title: Detailed Guide

Introduction explaining the concept...

## Section 1: Basic Concepts
Detailed explanation of fundamental concepts...

## Section 2: Implementation
Code examples and practical usage...

## Section 3: Common Patterns
Best practices and typical use cases...

## Section 4: Troubleshooting
Common errors and solutions...
```

## 🔧 **Prerequisites**

1. **Backend running**: Ensure FastAPI server is running
2. **Database setup**: PostgreSQL database should be initialized
3. **Environment**: Backend virtual environment activated

```bash
# From project root
cd backend
source venv/bin/activate  # or your venv activation
python start_server.py    # In separate terminal
```

## 🎯 **Next Steps**

After creating your topic:

1. **Test the Learning Flow**: Visit the frontend URL
2. **Check Components**: Verify didactic snippet and MCQs display correctly
3. **Refine Content**: Use the output JSON to review and improve content
4. **Create More Topics**: Use different source materials

## 🚨 **Troubleshooting**

### Error: "Material file not found"
- **Solution**: Check the file path and ensure the file exists

### Error: "Failed to save topic to database"
- **Solution**: Ensure backend database is running and accessible

### Error: "No such file or directory"
- **Solution**: Run the script from the `backend/` directory

### Frontend shows "No components"
- **Solution**: Check that both didactic snippet and MCQ components were created
- **Debug**: Use `--output` to inspect the generated content

## 🔄 **Integration with Frontend**

The created topic will work seamlessly with the simplified learning flow:

1. **Step 1**: Didactic snippet (learn the concept)
2. **Step 2-N**: Individual MCQs (test understanding)
3. **Completion**: Return to dashboard

This matches the current frontend expectation of individual MCQ steps!