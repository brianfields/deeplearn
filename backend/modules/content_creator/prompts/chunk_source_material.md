You are segmenting source material into lesson-sized chunks.

Inputs:
- Source material:
"""
{source_material}
"""
- Lesson titles (ordered): {lesson_titles}
- Desired number of lessons: {lesson_count}
- Target total minutes: {target_lesson_count}
- Recommended minutes per lesson: {per_lesson_minutes}
- Learner level: {user_level}

Guidelines:
- Create one chunk per lesson title; if titles are missing, choose sensible titles.
- Each chunk should be self-contained, referencing earlier chunks when helpful.
- Aim for ~{per_lesson_minutes} minutes of content per chunk.
- Include pointers to which unit LOs this chunk supports (inline in text where helpful).

Output (JSON matching schema exactly):
{{
  "chunks": [
    {{"index": 1, "title": "...", "chunk_text": "...", "estimated_minutes": 5}}
  ]
}}
