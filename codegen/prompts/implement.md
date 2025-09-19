Unheaded mode. You will implement code changes directly.

Project: {PROJECT}
Spec path: {SPEC_PATH}
Current progress: {CHECKED}/{TOTAL} checklist items complete.
Backend architecture reference: {BACKEND_ARCH}
Frontend architecture reference: {FRONTEND_ARCH}

Instructions:
- Read {SPEC_PATH}. Implement the next highest-priority unchecked item(s).
- Make minimal, high-quality edits only where needed. Do not add public interfaces or routes without need.
- Do backend tasks first and get *backend* tests to pass before doing frontend tasks.
- Use our modular architecture:
  - Follow all the rules in {BACKEND_ARCH} and {FRONTEND_ARCH}.
  - Keep names consistent across backend/frontend/mobile.
- Backward compatibility.
  - We do not need to worry about backward compatibility as we have yet to deploy the application. We can reset the database and start fresh.
- To avoid lint failures:
  - Use types on all function arguments and return values.
  - Preface any unused variables with an underscore.
- Implementation process:
  - After edits, update {SPEC_PATH} by marking completed items with "- [x] ...". If you add new tasks, justify briefly and add them, but prefer finishing existing items.
  - Stop when either all tasks are complete or there is nothing you can confidently check off.

Output format:
- Do not explain, but do note to the user what task you are working on and when you complete it so that they know what you are working on. Remember to also mark the task as complete in {SPEC_PATH} when it is complete.
