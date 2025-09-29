# Flow Engine Module — Agents Guide

The flow engine provides orchestration primitives: you define one or more steps, house them inside a flow, and execute the flow. Steps are executed by the engine as part of a flow, not by consumers directly.

- **Core model**: steps → grouped into a flow → the engine executes the flow.
- **Consumer policy**: do not execute steps directly. Create/retrieve a flow that contains one or more steps, then execute the flow. Step execution is internal to this module.
- **Why**: centralizing execution preserves ordering, retries, error handling, state tracking, and potential parallelism within the engine, allowing changes without breaking callers.

## Intended usage (conceptual)

```python
# Pseudocode — use this module's public/service APIs in the repo
# 1) Build or fetch a flow that contains ordered steps
flow = build_flow(steps=[step_a, step_b, step_c])

# 2) Execute the flow (the engine runs and manages its steps)
result = execute_flow(flow)

# 3) Observe results/status via the engine
status = result.status  # e.g., SUCCESS/FAILED, per-step outputs, logs
```

## Guidelines

1. **Execute flows, not steps**: wrap one or more steps in a flow; call the flow-level execution API.
2. **Keep orchestration in the engine**: retries, backoff, fan-out/fan-in, and state live here.
3. **Cross-module usage**: import only from this module’s `public` interface; within this module, routes use the service directly per project architecture.
4. **Minimal surface**: expose only what consumers need now; extend as new patterns emerge.
