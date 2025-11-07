# Instrumented Unit Generation Script

A comprehensive tool for generating learning units with full LLM request tracking and instrumentation.

## Overview

This script provides:
- **Full unit generation** from scratch with coach-driven learning objectives
- **Partial generation** modes for iterating on specific components (exercises, podcasts, artwork)
- **Comprehensive LLM tracking** - every prompt, response, and metadata saved to organized files
- **Config-driven** for reproducibility and easy iteration
- **Memorable IDs** for easy reference
- **One-lesson examples** for fast development cycles

## Quick Start

Generate a complete one-lesson unit:

```bash
cd backend
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json
```

See detailed progress:

```bash
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json --verbose
```

## Available Examples

Six ready-to-run config files covering different domains:

| Config File | Topic | Domain | Level |
|------------|-------|---------|-------|
| `roman_republic.json` | Fall of the Roman Republic | History | Intermediate |
| `react_fundamentals.json` | React Fundamentals | Programming | Beginner |
| `beginning_calculus.json` | Beginning Calculus | Math | Beginner |
| `superconductivity.json` | Superconductivity | Science | Advanced |
| `lean_startup.json` | Lean Startup | Business | Intermediate |
| `metaphysics.json` | Metaphysics | Philosophy | Intermediate |

## Output Structure

All outputs are written to `backend/logs/unit_creation/<memorable-id>/<timestamp>/`:

```
backend/logs/unit_creation/
  react-fundamentals/
    2025-11-07_14-30-45/
      config.json                              # Input configuration
      summary.json                             # Generation summary with costs

      01_learning_coach_generate_objectives/   # Each step gets a directory
        prompt.md                              # Pure prompt text
        response.md                            # Pure response text
        metadata.json                          # Model, tokens, cost, timing

      02_unit_creation_flow/
        prompt.md
        response.md
        metadata.json

      03_lesson_1_creation/
        prompt.md
        response.md
        metadata.json

      04_unit_podcast_generation/
        prompt.md
        response.md
        metadata.json

      05_unit_art_generation/
        prompt.md
        response.md
        metadata.json
```

### Why This Structure?

- **Separate files** - Easy to include prompts/responses in other work
- **Sequential numbering** - Clear execution order
- **Metadata isolation** - Prompts stay clean for reuse
- **Timestamped runs** - Compare iterations over time
- **Memorable IDs** - Easy to find and reference

## Full Unit Generation

Generates a complete unit from topic through artwork:

```bash
python scripts/generate_unit_instrumented.py --config scripts/examples/calculus.json
```

**Phases:**
1. **Learning Objectives** - Coach generates LOs from topic
2. **Unit Planning** - Generate/process source material, extract metadata
3. **Lesson Generation** - Create exercises, quizzes, and podcasts for each lesson
4. **Media** - Generate unit intro podcast and artwork

**Outputs:**
- Unit record in database
- All lessons with exercises and quizzes
- Lesson podcasts
- Unit intro podcast
- Unit artwork
- Complete LLM request history

## Partial Generation

Regenerate specific components for an existing unit:

### Regenerate Exercises

Re-run the lesson creation flow to generate new exercises and quizzes:

```bash
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/react_fundamentals.json \
  --only exercises \
  --unit-id <unit-id>
```

**Use case:** Iterating on exercise quality or prompt engineering

### Generate Podcasts

Create lesson and unit podcasts for an existing unit:

```bash
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/superconductivity.json \
  --only podcasts \
  --unit-id <unit-id>
```

**Use case:** Testing podcast generation or voice styles

### Generate Artwork

Create unit artwork:

```bash
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/metaphysics.json \
  --only artwork \
  --unit-id <unit-id>
```

**Use case:** Iterating on artwork prompts and styles

## Configuration File Format

```json
{
  "memorable_id": "short-descriptive-name",
  "topic": "Full Topic Name",
  "target_lessons": 1,
  "learner_level": "beginner|intermediate|advanced",
  "description": "Brief description for context",
  "source_material": null
}
```

**Fields:**
- `memorable_id` - Short ID for directory naming (lowercase-with-dashes)
- `topic` - The learning topic to generate content for
- `target_lessons` - Number of lessons (1 recommended for iteration)
- `learner_level` - Target audience: beginner, intermediate, or advanced
- `description` - Optional description (used for artwork generation)
- `source_material` - Optional pre-written content (null = generate from topic)

## LLM Request Tracking

Every LLM call is automatically tracked with:

### Prompt File (`prompt.md`)
Pure markdown with the system and user messages sent to the LLM. Ready to copy into other tools or tests.

### Response File (`response.md`)
Pure markdown with the LLM's response. Includes structured output for steps that use it.

### Metadata File (`metadata.json`)
```json
{
  "llm_request_id": "uuid",
  "provider": "openai",
  "model": "gpt-5-mini",
  "temperature": 1.0,
  "max_output_tokens": 8000,
  "status": "completed",
  "execution_time_ms": 2341,
  "input_tokens": 1523,
  "output_tokens": 487,
  "total_tokens": 2010,
  "cost_estimate": 0.0234,
  "cached": false,
  "created_at": "2025-11-07T14:30:45.123Z",
  "provider_response_id": "chatcmpl-...",
  "system_fingerprint": "fp_..."
}
```

### Summary File (`summary.json`)
Aggregated statistics for the entire run:
```json
{
  "unit_id": "uuid",
  "unit_title": "React Fundamentals",
  "lesson_count": 1,
  "lesson_titles": ["Introduction to React Components"],
  "lesson_ids": ["uuid"],
  "learning_objectives": [...],
  "llm_tracking": {
    "total_requests": 5,
    "total_cost_usd": 0.1234,
    "total_tokens": 12456,
    "requests_by_model": {
      "gpt-5-mini": 4,
      "gpt-5": 1
    },
    "steps": {
      "learning_coach_generate_objectives": 1,
      "unit_creation_flow": 1,
      "lesson_1_creation": 1,
      "unit_podcast_generation": 1,
      "unit_art_generation": 1
    }
  },
  "completed_at": "2025-11-07T14:35:23.456Z"
}
```

## Use Cases

### 1. Prompt Engineering
Iterate on prompts quickly with one-lesson units:
```bash
# Edit prompt in backend/modules/content_creator/prompts/
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json

# Review outputs in logs/unit_creation/react-fundamentals/<timestamp>/
# Compare with previous run
```

### 2. Quality Assessment
Review generated content systematically:
```bash
# Generate
python scripts/generate_unit_instrumented.py --config scripts/examples/calculus.json

# Review each step's outputs in sequence
# 01_* -> 02_* -> 03_* ...
```

### 3. Cost Analysis
Track LLM costs per component:
```bash
python scripts/generate_unit_instrumented.py --config scripts/examples/superconductivity.json

# Check summary.json for breakdown by step
```

### 4. Debugging
Full visibility into the generation pipeline:
```bash
python scripts/generate_unit_instrumented.py --config scripts/examples/lean_startup.json --verbose

# Check logs for each step
# Review prompt.md and response.md if output unexpected
```

### 5. Testing at Scale
Generate units across all domains:
```bash
for config in scripts/examples/*.json; do
  python scripts/generate_unit_instrumented.py --config $config
done
```

## Comparison with Original Script

| Feature | Old `create_unit.py` | New `generate_unit_instrumented.py` |
|---------|---------------------|-----------------------------------|
| LLM tracking | ❌ None | ✅ Full tracking with files |
| Partial generation | ❌ No | ✅ Yes (exercises, podcasts, artwork) |
| Config-driven | ❌ CLI args only | ✅ JSON configs |
| Examples | ❌ None | ✅ 6 ready-to-run examples |
| Output organization | ❌ DB only | ✅ Files + DB |
| Memorable IDs | ❌ No | ✅ Yes |
| Iteration speed | Medium | ✅ Fast (one-lesson) |
| Prompt reuse | ❌ Hard | ✅ Easy (separate files) |

## Tips

### Fast Iteration
Use one-lesson configs and partial generation:
```bash
# Generate unit once
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json

# Iterate on exercises only
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/react_fundamentals.json \
  --only exercises \
  --unit-id <unit-id>
```

### Compare Runs
Use memorable IDs to track iterations:
```bash
ls -la backend/logs/unit_creation/react-fundamentals/
# Shows all runs chronologically
```

### Copy Prompts
Prompts are clean markdown ready for reuse:
```bash
cat backend/logs/unit_creation/react-fundamentals/2025-11-07_14-30-45/03_lesson_1_creation/prompt.md
```

### Check Costs
Before scaling up:
```bash
# Run one example
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json

# Check summary.json for total_cost_usd
# Multiply by number of units to estimate
```

## Requirements

- Python 3.11+
- All backend dependencies installed
- Database initialized
- Environment variables configured (LLM API keys, etc.)
- Infrastructure provider initialized

## Architecture

Uses **Direct Flow Invocation** (Option B):
- Calls flows directly without system changes
- Maximum flexibility for iteration
- Zero impact on production code
- Perfect for development and prompt engineering

## See Also

- `backend/scripts/examples/README.md` - Example configs documentation
- `backend/modules/content_creator/flows.py` - Flow definitions
- `backend/modules/content_creator/prompts/` - LLM prompts
