# Fast Flow - User Description

The user wants to create a "fast_flow" feature that addresses performance issues in the current content creation flow implementation in `content_creator/`.

## Problem Statement
The current flow implementation takes a long time to run because it:
- Makes separate LLM calls for each component (learning objectives, misconceptions, didactic snippet, glossary)
- Creates lessons sequentially rather than in parallel

## Desired Solution
Create a fast running version that produces the same models but with optimizations:
1. **Single LLM call for lesson components**: Instead of separate queries for learning objectives, misconceptions, didactic snippet, and glossary, make one comprehensive LLM call to extract all components at once
2. **Parallel lesson creation**: When creating units with multiple lessons, create the lessons in parallel instead of sequentially
3. **Maintain same public interface**: The fast version should be available alongside the current one in the public interface, allowing users to choose between speed and the current approach

## Expected Outcomes
- Significantly faster content creation while maintaining the same quality and data models
- Same public interfaces and return types as the existing implementation
- Option for users to choose between the standard flow and the fast flow