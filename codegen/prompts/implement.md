Unheaded mode. You will implement code changes directly.

Project: {PROJECT}
Spec path: {SPEC_PATH}
Current progress: {CHECKED}/{TOTAL} checklist items complete.
Backend architecture reference: {BACKEND_ARCH}
Frontend architecture reference: {FRONTEND_ARCH}

Instructions:
- Read {SPEC_PATH}. Implement the next highest-priority unchecked item(s).
- Make minimal, high-quality edits only where needed. Do not add public interfaces or routes without need.
- Follow all the rules in {BACKEND_ARCH} and {FRONTEND_ARCH}.
- Keep names consistent across backend/frontend/mobile.
- We do not need to worry about backward compatibility as we have yet to deploy the application. We can reset the database and start fresh.
- After edits, update {SPEC_PATH} by marking completed items with "- [x] ...". If you add new tasks, justify briefly and add them, but prefer finishing existing items.
- Stop when either all tasks are complete or there is nothing you can confidently check off.

Output format:
- Do not explain. Just make edits to the repository and update {SPEC_PATH}.
