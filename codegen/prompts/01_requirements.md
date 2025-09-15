Goal: Determine the requirements for the project "{PROJECT}" through a conversation with the user.
Context: The user's description of the project is in {USER_DESCRIPTION}.

First, examine the code to understand the context for this project.

After you've examined the code, ask the user for any necessary clarifications to their description of the project that aren't clear from the combination of the code and their description. This can go on for a few rounds.

When you have a good understanding of the project, create a project requirements document for the project and write it to {OUT_REQUIREMENTS}. Do not write any application code; we want concise description of the high-level requirements to be used in subsequent steps.

Once you've written the requirements document, ask the user to review and ask for any revisions. Once the user is satisfied, you will exit (or tell the user to exit).