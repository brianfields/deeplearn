# 🎤 Podcast Module Usage Guide

This guide shows you how to use the podcast generation functionality in the DeepLearn platform.

## 📋 Prerequisites

1. **API Keys**: Set up your OpenAI API key in the environment
2. **Database**: Ensure the database is running and migrated
3. **Topics**: Have existing topics in the database to generate podcasts from

## 🚀 Quick Start

### 1. Start the Server

```bash
cd backend
source ../deeplearn/bin/activate
python start_server.py
```

The server will start on `http://localhost:8000`

### 2. Generate Your First Podcast

#### Step 1: Create a Topic (if you don't have one)

```bash
curl -X POST "http://localhost:8000/api/content-creation/topics" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Neural Networks",
    "source_material": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information. Each neuron receives input, applies a function, and produces output. Neural networks can learn patterns from data through training.",
    "source_domain": "Machine Learning",
    "source_level": "intermediate"
  }'
```

This will return a topic with an ID like `"topic-id-123"`.

#### Step 2: Generate Podcast from Topic

```bash
curl -X POST "http://localhost:8000/api/content-creation/podcasts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "topic-id-123",
    "generate_audio": false
  }'
```

**Response:**
```json
{
  "episode_id": "episode-456",
  "title": "Educational Podcast on Neural Networks",
  "description": "Educational podcast covering 3 key concepts",
  "total_duration_minutes": 4,
  "learning_outcomes": [
    "Explain the basic structure of neural networks",
    "Describe how neurons process information"
  ],
  "segments": [
    {
      "segment_type": "intro_hook",
      "title": "Introduction to Neural Networks",
      "content": "Welcome to our educational journey!...",
      "estimated_duration_seconds": 35,
      "learning_outcomes": [],
      "tone": "conversational_educational",
      "word_count": 89
    }
  ],
  "full_script": "Welcome to our educational journey! Have you ever wondered about Neural Networks?...",
  "status": "generated"
}
```

### 3. Retrieve Your Podcast

#### Get by Episode ID:
```bash
curl "http://localhost:8000/api/content-creation/podcasts/episode-456"
```

#### Get by Topic ID:
```bash
curl "http://localhost:8000/api/content-creation/podcasts/topic/topic-id-123"
```

## 📚 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/content-creation/podcasts/generate` | Generate podcast from topic |
| `GET` | `/api/content-creation/podcasts/{episode_id}` | Get podcast by episode ID |
| `GET` | `/api/content-creation/podcasts/topic/{topic_id}` | Get podcast by topic ID |

### Request Models

#### PodcastGenerationRequest
```json
{
  "topic_id": "string",
  "generate_audio": false
}
```

### Response Models

#### PodcastGenerationResponse
```json
{
  "episode_id": "string",
  "title": "string",
  "description": "string",
  "total_duration_minutes": 4,
  "learning_outcomes": ["string"],
  "segments": [...],
  "full_script": "string",
  "status": "generated"
}
```

## 🎯 Features

### ✅ What the Podcast Module Does

1. **Learning Outcome Extraction**: Automatically extracts learning outcomes from existing topics
2. **Structure Planning**: Creates 3-6 minute podcast structures with proper timing
3. **Script Generation**: Generates conversational, educational scripts
4. **Segment Organization**: Creates 4 segments (intro, overview, main content, summary)
5. **Database Persistence**: Saves podcasts to database for later retrieval
6. **Quality Validation**: Ensures scripts meet timing and content requirements

### 📊 Podcast Structure

Each generated podcast has:

- **Intro Hook** (30-45 seconds): Engaging introduction
- **Overview** (30-45 seconds): Preview of learning outcomes
- **Main Content** (2-3 minutes): Detailed explanation with examples
- **Summary** (30-45 seconds): Key takeaways and closure

### 🎨 Script Characteristics

- **Duration**: 3-6 minutes (180-360 seconds)
- **Tone**: Conversational and educational
- **Style**: Lecture-style for MVP
- **Content**: Based on topic's learning objectives
- **Transitions**: Natural flow between segments

## 🔧 Advanced Usage

### Direct Service Usage (Python)

```python
from src.modules.podcast.service import PodcastService
from src.core.service_base import ServiceConfig
from src.llm_interface import LLMConfig, LLMProviderType

# Initialize service
llm_config = LLMConfig(provider=LLMProviderType.OPENAI)
service_config = ServiceConfig(llm_config=llm_config)
podcast_service = PodcastService(service_config, llm_client)

# Generate podcast
script = await podcast_service.generate_podcast_script("topic-id")

# Save to database
episode_id = db_service.save_podcast_episode(script, "topic-id")

# Retrieve podcast
episode = await podcast_service.get_podcast_episode(episode_id)
```

### Structure Planning Only

```python
# Plan structure without generating full script
structure = await podcast_service.plan_podcast_structure(
    learning_outcomes=["Explain neural networks", "Describe neurons"],
    topic_title="Neural Networks"
)
```

## 🚨 Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Topic not found` | Invalid topic ID | Use valid topic ID from database |
| `No learning outcomes provided` | Empty topic or no learning objectives | Ensure topic has learning objectives |
| `Script duration outside range` | Generated script too short/long | This is handled automatically |
| `Database service not available` | Database connection issue | Check database configuration |

## 🔮 Future Enhancements

The podcast module is designed for extensibility:

- **Audio Generation**: Future audio file generation
- **Multiple Topics**: Link multiple topics to single podcast
- **Custom Durations**: Support for longer/shorter podcasts
- **Different Styles**: Support for different podcast styles
- **Advanced Editing**: Script editing and refinement tools

## 📝 Example Workflow

1. **Create Topic**: Use existing topic creation API
2. **Generate Podcast**: Call podcast generation API
3. **Review Script**: Check the generated script content
4. **Retrieve Later**: Use episode ID or topic ID to retrieve
5. **Use in App**: Integrate with your learning application

## 🎯 MVP Limitations

For the MVP, the podcast module:

- ✅ Generates 3-6 minute educational podcasts
- ✅ Uses existing topic learning objectives
- ✅ Creates lecture-style content
- ✅ Saves to database for retrieval
- ⚠️ Scripts are slightly shorter than ideal (acceptable for MVP)
- ⚠️ No audio generation (script only)
- ⚠️ One topic per podcast (designed for future extension)

The module is production-ready for educational podcast generation! 🎤📚
