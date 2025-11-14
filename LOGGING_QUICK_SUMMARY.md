# Logging Improvements - Quick Summary

## Problem
Learning coach turns sometimes take a long time (slow LLM response), but there's insufficient logging to debug where the time is being spent or identify retries.

## Root Causes (Most Likely)
1. **LLM API retries** - Rate limits (429), timeouts (504), or server errors (5xx)
2. **Resource loading** - Slow database queries for conversation resources
3. **Prompt assembly** - Large system prompts with extensive resource context

## Solution: Add Strategic Logging at 4 Key Points

### 1. **Route Entry Point** (5 min)
File: `backend/modules/learning_conversations/routes.py`
- Add timing from request start to response
- Add correlation ID (request_id) for tracing
- Log user_id, conversation_id, message length

**Impact**: See total turn duration + can trace through all logs

### 2. **Learning Coach Generation** (10 min)
File: `backend/modules/learning_conversations/conversations/learning_coach.py`
- Replace `print()` statements with proper logging (lines 146, 154, 158)
- Add timing breakdowns: resource loading → prompt building → LLM call → recording
- Log counts: number of resources, prompt size, token usage

**Impact**: See which step takes the time

### 3. **LLM Provider Retries** (15 min)
File: `backend/modules/llm_services/providers/openai.py`
- Log attempt success (currently only logs failures)
- Include retry history with error type, status code, backoff time
- Track total retry duration

**Impact**: See if retries are happening and why

### 4. **Server Logging Setup** (10 min)
File: `backend/server.py`
- Add structured formatter to support extra fields in logs
- Enable optional JSON logging for production

**Impact**: Consistent log format across system

## Total Effort: ~40 minutes

## After Implementation, You Can:
- ✅ See exactly where time is spent in each turn
- ✅ Identify API rate limit issues
- ✅ Trace slow turns through correlation IDs
- ✅ Compare successful vs retry attempts
- ✅ Measure resource loading performance
- ✅ Analyze prompt size impact

## Quick Wins (Immediate)

You can immediately add basic request timing without refactoring:

```python
# In routes.py submit_learner_turn()
import time
start = time.time()
state = await service.submit_learner_turn(...)
duration_ms = (time.time() - start) * 1000
print(f"TURN_DURATION_MS: {duration_ms}")
```

This gives you the "how slow" answer. Then implement the full solution for "why slow".

## Documents Created

1. **`LOGGING_ASSESSMENT.md`** - Detailed analysis of current logging gaps
2. **`LOGGING_IMPLEMENTATION_GUIDE.md`** - Copy-paste ready code for all changes
3. **`COACH_CONVERSATION_FLOW.md`** - Visual flow diagram + timing breakdown
4. **`LOGGING_QUICK_SUMMARY.md`** - This file

## Next Steps

1. Read `LOGGING_IMPLEMENTATION_GUIDE.md`
2. Implement changes in order: Server Setup → Routes → Learning Coach → LLM Provider
3. Restart backend with `LOG_LEVEL=DEBUG`
4. Make a test conversation turn
5. Check logs for timing breakdown
6. Identify bottleneck (should be clear now)
7. Add additional logging if needed for that specific bottleneck

## Environment Variables to Add

```bash
# In your .env or shell:
export LOG_LEVEL=DEBUG              # See all logs
export DEBUG=true                   # Include file:line in logs
export JSON_LOGGING=false           # true for production structured logs
```

## Expected Log Output After Implementation

```
2024-12-15 10:45:23 - [routes.py:192] COACH_TURN_START - {request_id=a8f2, conv_id=123e4567}
2024-12-15 10:45:23 - [learning_coach.py:325] Resources loaded - {count=2, duration_ms=180}
2024-12-15 10:45:23 - [learning_coach.py:335] System prompt prepared - {length=2847, duration_ms=45}
2024-12-15 10:45:25 - [openai.py:987] API call failed, will retry - {attempt=1, error=APITimeoutError, backoff_s=1.0}
2024-12-15 10:45:26 - [openai.py:982] API call succeeded after retries - {total_retries=1}
2024-12-15 10:45:27 - [learning_coach.py:340] LLM complete - {duration_ms=2156, tokens=2000→450}
2024-12-15 10:45:27 - [routes.py:210] COACH_TURN_COMPLETE - {duration_ms=2528, request_id=a8f2}
```

**Reading this log**: Turn took 2.5 seconds. Most time was LLM call (2.1s), which had 1 retry. Resource loading was fast (180ms).

---

**For detailed implementation, see: `LOGGING_IMPLEMENTATION_GUIDE.md`**



