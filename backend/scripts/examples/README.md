# Instrumented Unit Generation Examples

This directory contains ready-to-run configuration files for generating one-lesson learning units across different domains.

## Quick Start

Generate a unit using any of these examples:

```bash
# History - Fall of the Roman Republic
python scripts/generate_unit_instrumented.py --config scripts/examples/roman_republic.json

# Programming - React Fundamentals
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json

# Math - Beginning Calculus
python scripts/generate_unit_instrumented.py --config scripts/examples/beginning_calculus.json

# Science - Superconductivity
python scripts/generate_unit_instrumented.py --config scripts/examples/superconductivity.json

# Business - Lean Startup
python scripts/generate_unit_instrumented.py --config scripts/examples/lean_startup.json

# Philosophy - Metaphysics
python scripts/generate_unit_instrumented.py --config scripts/examples/metaphysics.json
```

## Output

All output files are written to:
```
backend/logs/unit_creation/<memorable-id>/<timestamp>/
```

For example:
```
backend/logs/unit_creation/roman-republic-fall/2025-11-07_14-30-45/
  config.json                              # Generation config
  summary.json                             # Results summary
  01_learning_coach_generate_objectives/   # Each LLM call gets a directory
    prompt.md                              # Just the prompt
    response.md                            # Just the response
    metadata.json                          # Model, tokens, cost, etc.
  02_unit_creation_flow/
    prompt.md
    response.md
    metadata.json
  03_lesson_1_creation/
    ...
  04_unit_podcast_generation/
    ...
  05_unit_art_generation/
    ...
```

## Verbose Mode

See detailed progress:

```bash
python scripts/generate_unit_instrumented.py --config scripts/examples/react_fundamentals.json --verbose
```

## Configuration Format

Each config file is a JSON file with these fields:

```json
{
  "memorable_id": "short-descriptive-name",
  "topic": "Full Topic Name",
  "target_lessons": 1,
  "learner_level": "beginner|intermediate|advanced",
  "description": "Brief description of what the unit covers",
  "source_material": null
}
```

- `memorable_id`: Used for directory naming (lowercase-with-dashes)
- `topic`: The learning topic
- `target_lessons`: Number of lessons (all examples use 1 for fast iteration)
- `learner_level`: Target audience level
- `description`: Optional description for artwork/context
- `source_material`: Optional pre-written content (null = generate from topic)

## Partial Generation (Coming Soon)

Regenerate only specific portions of an existing unit:

```bash
# Regenerate only exercises for a unit
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/react_fundamentals.json \
  --only exercises \
  --unit-id <unit-id>

# Generate only podcasts
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/calculus.json \
  --only podcasts \
  --unit-id <unit-id>

# Generate only artwork
python scripts/generate_unit_instrumented.py \
  --config scripts/examples/superconductivity.json \
  --only artwork \
  --unit-id <unit-id>
```

## Use Cases

This instrumented generation is perfect for:

1. **Prompt Engineering**: Easy access to all prompts and responses
2. **Quality Assessment**: Review generated content step-by-step
3. **Cost Analysis**: Track token usage and costs per step
4. **Debugging**: Full visibility into the generation pipeline
5. **Iteration**: Fast one-lesson generation for testing changes
