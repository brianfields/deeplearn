# User Description: Redo Exercise Generation

Note that we are already generating MCQ and short answer exercises as part of lesson plan generation. I'm working on a refinement of this generation. I've written some new prompts but have yet to adjust the code. 

The new prompt flow is:
1. extract_concept_glossary.md
2. annotate_concept_glossary.md
3. generate_comprehension_exercises.md
4. generate_transfer_exercises.md
5. generate_quiz_from_questions.md

Note that the output structures are a bit different for these prompts; so code in both front and backend might need to change. 

Also note that I'm now constructing a quiz explicitly as opposed to just running through all MCQ followed by short answer. 

The goal is to move from the old exercise generation scheme to the new one, storing all relevant information in the database and having it all available on the frontend (mobile and admin).
