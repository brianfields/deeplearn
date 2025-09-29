## learning_session module

This module tracks a learner’s progress through a single lesson and rolls it up at the unit level.

### LearningSessionModel — how it’s used
- Created when a user starts a lesson; `total_exercises` is computed from lesson content.
- Updated on each exercise submission to advance `current_exercise_index`, increment `exercises_completed` (first completion only), increment `exercises_correct` (on first-ever correct), and recompute `progress_percentage`.
- Completed when the lesson is finished; results are calculated from counts stored on the session.

### UnitSessionModel — how it’s used
- Persistent per-user, per-unit progress store.
- Ensured on session start if the lesson belongs to a unit.
- On session completion, the completed lesson is recorded; unit `progress_percentage` is updated and the unit may be marked completed when all lessons are done.

### How individual exercise attempts are tracked
- Stored in `LearningSessionModel.session_data.exercise_answers[exercise_id]`.
- Each submission appends an entry to `attempt_history` with `attempt_number`, `is_correct`, `user_answer`, `time_spent_seconds`, and `submitted_at`.
- `has_been_answered_correctly` becomes true after the first correct submission and stays true.
- Only actual exercises contribute to counts and percentage; UI-only components are ignored.
