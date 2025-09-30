# Content-Async Feature Description

## User Input

Notice that the content module's public interface is mostly sync, but some of it is async. That's complicated. I'd like to make it all async and change all call sites to adapt to that. I'm hoping that will reduce the amount of code and make things simpler.

## Summary

The content module currently has a mixed sync/async public interface, which adds complexity. The goal is to standardize the entire public interface to be async and update all calling code accordingly. This refactoring should simplify the codebase and reduce code complexity.