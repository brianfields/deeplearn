Unheaded mode. You will fix modular architecture issues and check off items.

Project directory: {PROJECT_DIR}
- Backend checklist (project-local): {BACKEND_CHECKLIST}
- Frontend checklist (project-local): {FRONTEND_CHECKLIST}

Instructions:
- Open and read both checklists. For each unchecked item, inspect the codebase and make the minimal edits needed to satisfy the rule, following our architecture docs.
- Only change code that is necessary to meet the checklist items. Avoid adding public APIs or routes unless there is a current consumer.
- When an item is satisfied, update the corresponding checklist file to mark it with "- [x]".
- Prefer small, clear edits preserving behavior. Add explicit return types on functions where missing.
- Continue until no unchecked items remain or no further items can be confidently satisfied.

Output format:
- Do not explain. Make repository edits and update the checklist files at {BACKEND_CHECKLIST} and {FRONTEND_CHECKLIST}.
