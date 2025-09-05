## Structured Data Pass

You are an expert instructional designer.

Your task: Convert the following unstructured source material into **refined material** that will later be used to create multiple-choice questions.

Follow these rules carefully:

1. **Segment into topics**
   - Read the source material and break it into clear topics or subtopics.
   - Each topic should cover one coherent concept.

2. **For each topic, generate:**
   - `learning_objectives`: 2–5 statements of what a learner should be able to do.
     - Use action verbs (identify, explain, differentiate, apply, evaluate).
     - Include an estimated Bloom's taxonomy level in parentheses after each.
   - `key_facts`: concise bullet-point style statements of essential facts, principles, or relationships.
   - `common_misconceptions`: a list of misconception objects, each with:
     - `misconception`: the incorrect belief.
     - `correct_concept`: the correct idea.
   - `assessment_angles`: notes on how each objective or concept might be assessed with an MCQ later (e.g., "ask for definition," "apply concept in scenario," etc.).

3. **Be concise and declarative**
   - Do not copy long sentences verbatim.
   - No filler words. Just the essentials.

4. **Output format**
   - Return a single JSON object with this structure:

```json
{
  "topics": [
    {
      "topic": "string",
      "learning_objectives": [
        "string (Bloom level)",
        "string (Bloom level)"
      ],
      "key_facts": [
        "string",
        "string"
      ],
      "common_misconceptions": [
        {
          "misconception": "string",
          "correct_concept": "string"
        }
      ],
      "assessment_angles": [
        "string",
        "string"
      ]
    }
  ]
}
```

**Now process the following unstructured material:**

[PASTE YOUR SOURCE MATERIAL HERE]
