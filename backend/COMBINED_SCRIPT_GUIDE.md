# 🎯 Combined Topic & Podcast Creation Script

This guide shows you how to use the `create_topic_and_podcast.py` script that combines both topic creation and podcast generation in one workflow.

## 🚀 Quick Start

### Basic Usage
```bash
python scripts/create_topic_and_podcast.py \
    --topic "Neural Networks" \
    --concept "Neural Network Basics" \
    --material scripts/examples/cross_entropy_material.txt \
    --verbose
```

### With JSON Output
```bash
python scripts/create_topic_and_podcast.py \
    --topic "PyTorch Cross-Entropy Loss" \
    --concept "Cross-Entropy Loss Function" \
    --material scripts/examples/cross_entropy_material.txt \
    --output combined_output.json \
    --verbose
```

## 📋 What the Script Does

The script performs a complete workflow:

### **Step 1: Topic Creation**
- ✅ Reads source material from file
- ✅ Generates didactic snippet with learning objectives
- ✅ Creates glossary with key terms
- ✅ Generates multiple choice questions
- ✅ Saves complete topic to database

### **Step 2: Podcast Generation**
- ✅ Extracts learning outcomes from the created topic
- ✅ Plans 3-6 minute podcast structure
- ✅ Generates conversational, educational script
- ✅ Creates 4 segments (intro, overview, main content, summary)
- ✅ Saves podcast episode to database

### **Step 3: Results**
- ✅ Returns topic ID and episode ID
- ✅ Provides API URLs for both topic and podcast
- ✅ Optionally saves complete content to JSON file

## 🎯 Command Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--topic` | ✅ | Topic title |
| `--concept` | ✅ | Core concept to focus on |
| `--material` | ✅ | Path to source material text file |
| `--level` | ❌ | Target user level (beginner/intermediate/advanced) |
| `--domain` | ❌ | Subject domain (default: "Machine Learning") |
| `--verbose` | ❌ | Show detailed progress and service logs |
| `--debug` | ❌ | Enable debug logging (includes OpenAI API calls) |
| `--output` | ❌ | Save combined content to JSON file |

## 📄 Example Output

When successful, you'll see:
```
🎯 Creating topic and podcast workflow
==================================================
📋 Topic: Neural Networks
🎯 Core Concept: Neural Network Basics
📚 User Level: intermediate
🏷️  Domain: Machine Learning

🔄 Step 1: Generating complete topic content...
✅ Generated complete topic content!
   • Didactic snippet: Understanding Neural Networks
   • Glossary entries: 5
   • Multiple choice questions: 3

🔄 Step 2: Saving topic to database...
✅ Topic saved with ID: topic-123

🔄 Step 3: Generating podcast from topic...
✅ Podcast generated with episode ID: episode-456

🎉 Topic and podcast creation completed successfully!
   • Topic ID: topic-123
   • Episode ID: episode-456
   • Topic URL: http://localhost:3000/learn/topic-123?mode=learning
   • Podcast API: http://localhost:8000/api/content-creation/podcasts/episode-456
   • Topic Podcast API: http://localhost:8000/api/content-creation/podcasts/topic/topic-123
```

## 📁 JSON Output Format

If you use `--output`, you'll get a comprehensive JSON file with:

```json
{
  "topic_id": "topic-123",
  "episode_id": "episode-456",
  "topic_title": "Neural Networks",
  "core_concept": "Neural Network Basics",
  "user_level": "intermediate",
  "domain": "Machine Learning",
  "topic_content": {
    "didactic_snippet": {...},
    "glossary": {...},
    "mcqs": [...]
  },
  "podcast_script": {
    "title": "Educational Podcast on Neural Networks",
    "description": "Educational podcast covering 3 key concepts",
    "total_duration_seconds": 240,
    "learning_outcomes": [...],
    "segments": [...],
    "full_script": "Welcome to our educational journey!..."
  },
  "generated_at": "2024-07-27T19:13:00"
}
```

## 🔧 Prerequisites

1. **Virtual Environment**: Activate the deeplearn environment
   ```bash
   source ../deeplearn/bin/activate
   ```

2. **API Keys**: Set up your OpenAI API key in the environment

3. **Database**: Ensure the database is running and migrated

4. **Source Material**: Have a text file with educational content

## 📝 Example Source Material

Create a text file (e.g., `neural_networks.txt`) with content like:
```
Neural networks are computational models inspired by biological neural networks.
They consist of interconnected nodes (neurons) that process information.
Each neuron receives input, applies a function, and produces output.
Neural networks can learn patterns from data through training.

Key concepts include:
- Neurons and activation functions
- Forward and backward propagation
- Loss functions and optimization
- Training and validation
```

## 🎤 What You Get

### **Topic Components**
- **Didactic Snippet**: Educational explanation with learning objectives
- **Glossary**: Key terms and definitions
- **MCQs**: Multiple choice questions for assessment

### **Podcast Episode**
- **Duration**: 3-6 minutes (180-360 seconds)
- **Segments**: 4 structured segments
- **Style**: Conversational and educational
- **Content**: Based on topic learning objectives

## 🔗 API Access

After creation, you can access:

- **Topic**: `http://localhost:3000/learn/{topic_id}?mode=learning`
- **Podcast by Episode**: `http://localhost:8000/api/content-creation/podcasts/{episode_id}`
- **Podcast by Topic**: `http://localhost:8000/api/content-creation/podcasts/topic/{topic_id}`

## 🚨 Error Handling

The script handles common errors:
- Missing source material file
- Database connection issues
- API key configuration problems
- Invalid topic/concept parameters

## 🎯 Use Cases

Perfect for:
- **Quick Content Creation**: Generate both topic and podcast in one command
- **Educational Content**: Create learning materials with audio components
- **Prototyping**: Rapidly test topic and podcast generation
- **Batch Processing**: Create multiple topics with podcasts

## 🚀 Ready to Use!

The combined script is production-ready and provides a complete workflow from source material to both topic and podcast generation. Just provide your source material and let the AI do the rest! 🎤📚
