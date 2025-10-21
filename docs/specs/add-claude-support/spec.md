# Spec: Add Claude Support to LLM Services

## User Story

**As a** developer using the deeplearn platform  
**I want** the ability to use Claude models (via Anthropic API or AWS Bedrock) in addition to OpenAI  
**So that** I can leverage Claude's capabilities for specific flows, conversations, and content creation tasks based on their strengths (e.g., speed with Haiku, reasoning with Opus)

### User Experience Changes

**Backend/Configuration:**
- Developers can configure Claude access via environment variables (`ANTHROPIC_API_KEY` or AWS Bedrock credentials)
- Developers can specify Claude models explicitly when creating flows, conversations, or making LLM calls:
  - `claude-sonnet-4-5` - For complex agents and coding ($3/$15 per MTok)
  - `claude-haiku-4-5` - Fastest with near-frontier intelligence ($1/$5 per MTok) 
  - `claude-opus-4-1` - For specialized reasoning ($15/$75 per MTok)
- The system automatically routes to the appropriate provider based on the model name
- All Claude requests are logged with full metadata (model, provider, tokens, cost) just like OpenAI requests

**Admin Dashboard:**
- LLM request logs continue to show model name, which now includes Claude models
- Cost estimates reflect Claude pricing automatically
- No additional UI changes needed

**Mobile/Frontend:**
- No changes needed (backend-only feature)
- Any content generated with Claude models will be tracked with the model name in metadata

**Developer API:**
- Flows can specify `model="claude-haiku-4-5"` in step configuration
- Conversations can specify `model="claude-opus-4-1"` for reasoning-heavy tasks
- Content creator can use Claude for podcast generation by specifying the model
- If a Claude model is specified for unsupported operations (image/audio generation), clear exceptions are raised

---

## Requirements Summary

### What to Build

1. **Claude Provider Implementation** - Add support for Claude models via two access methods:
   - Direct Anthropic API (using `anthropic` Python SDK)
   - AWS Bedrock (using `boto3` with bedrock-runtime)

2. **Model Support** - Support three Claude models:
   - `claude-sonnet-4-5` - Smart model for complex tasks
   - `claude-haiku-4-5` - Fastest model (default for Claude)
   - `claude-opus-4-1` - Best reasoning model

3. **Configuration** - Environment-variable based configuration:
   - Support either Anthropic Direct OR AWS Bedrock (mutually exclusive, configured via env vars)
   - Default AWS region: `us-west-2`

4. **Cost Tracking** - Accurate cost estimation using Claude pricing:
   - Sonnet 4.5: $3 input / $15 output per MTok
   - Haiku 4.5: $1 input / $5 output per MTok
   - Opus 4.1: $15 input / $75 output per MTok

5. **Feature Parity** - Support the following operations:
   - ✅ Text generation (`generate_response`)
   - ✅ Structured outputs (`generate_structured_object`)
   - ❌ Image generation - Raise `NotImplementedError` (Claude doesn't support)
   - ❌ Audio generation - Raise `NotImplementedError` (Claude doesn't support)
   - ❌ Web search - Raise `NotImplementedError` (Claude doesn't support)

### Constraints

- Model name implies the provider (e.g., `claude-*` routes to Claude, `gpt-*` routes to OpenAI)
- No backward compatibility code needed
- No UI changes required beyond what's already tracked (model name in logs)
- No migration of existing data
- Only one Claude access method active at a time (Anthropic Direct OR Bedrock)

### Acceptance Criteria

- [ ] Can configure Anthropic Direct API via `ANTHROPIC_API_KEY`
- [ ] Can configure AWS Bedrock via AWS credentials and region
- [ ] Can call `generate_response()` with `model="claude-haiku-4-5"` and get valid response
- [ ] Can call `generate_structured_object()` with Claude models and get valid parsed objects
- [ ] Calling unsupported operations (image/audio) with Claude models raises clear exceptions
- [ ] All Claude requests are logged to `llm_requests` table with correct provider, model, tokens, and cost
- [ ] Integration tests can specify Claude models and validate responses
- [ ] Cost estimates use Claude pricing correctly
- [ ] Admin dashboard shows Claude requests with model names
- [ ] Flows and conversations can specify Claude models

---

## Cross-Stack Module Mapping

### Backend: `backend/modules/llm_services/`

This is the **only** backend module that needs changes.

**Files to modify:**
1. `types.py` - Add `BEDROCK` provider type to enum
2. `config.py` - Add configuration support for Anthropic/Bedrock credentials
3. `providers/factory.py` - Update factory to route model names to appropriate provider
4. `test_llm_services_unit.py` - Add unit tests for Claude providers

**Files to create:**
1. `providers/claude.py` - New provider implementations:
   - Helper functions (module-level):
     - `estimate_claude_cost()` - Cost calculation for Claude models
     - `convert_to_claude_messages()` - Message format conversion
     - `parse_claude_response()` - Response parsing
     - `get_claude_model_config()` - Model metadata (context window, max tokens, etc.)
   - `AnthropicProvider(LLMProvider)` - Direct Anthropic API implementation
   - `BedrockProvider(LLMProvider)` - AWS Bedrock implementation

**Files unchanged:**
- `models.py` - Already tracks provider/model dynamically
- `repo.py` - No changes needed
- `service.py` - Provider abstraction handles everything
- `public.py` - No interface changes
- `routes.py` - No changes needed
- `cache.py` - Works with any provider
- `exceptions.py` - Existing exceptions sufficient
- `providers/base.py` - Interface already defined
- `providers/openai.py` - No changes

### Backend: Integration Tests

**Files to modify:**
1. `backend/tests/test_lesson_creation_integration.py` - Add ability to test with specified model (including Claude)

### Backend: Seed Data

**Files to modify:**
1. `backend/scripts/create_seed_data.py` - No changes needed (uses default OpenAI models)

### Frontend: Admin

**No changes needed** - Admin dashboard already displays model names dynamically in LLM request logs.

### Frontend: Mobile

**No changes needed** - Model selection happens at backend level only.

---

## Implementation Checklist

### Backend: LLM Services Module

- [ ] Update `types.py`: Add `BEDROCK = "bedrock"` to `LLMProviderType` enum
- [ ] Update `config.py`: Add Anthropic/Bedrock configuration
  - Add `anthropic_api_key`, `anthropic_model`, `bedrock_model_id`, `aws_region` fields to `LLMConfig`
  - Update `create_llm_config_from_env()` to read `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `BEDROCK_MODEL_ID`
  - Add logic to determine provider based on available credentials
- [ ] Create `providers/claude.py`: Implement Claude providers
  - Add helper function `estimate_claude_cost(input_tokens, output_tokens, model)` with Claude pricing
  - Add helper function `convert_to_claude_messages(messages)` to convert internal messages to Claude format
  - Add helper function `parse_claude_response(response)` to extract content/tokens from Claude response
  - Add helper function `get_claude_model_config(model)` to return model metadata (context window, max output, etc.)
  - Implement `AnthropicProvider(LLMProvider)`:
    - Initialize `anthropic.AsyncAnthropic` client
    - Implement `generate_response()` using `client.messages.create()`
    - Implement `generate_structured_object()` using Claude's JSON mode
    - Implement `generate_image()` to raise `NotImplementedError` with clear message
    - Implement `generate_audio()` to raise `NotImplementedError` with clear message
    - Implement `search_recent_news()` to raise `NotImplementedError` with clear message
    - Add retry logic with exponential backoff for rate limits
    - Add error conversion from Anthropic exceptions to LLM exceptions
  - Implement `BedrockProvider(LLMProvider)`:
    - Initialize `boto3.client('bedrock-runtime')` with AWS credentials
    - Implement `generate_response()` using `client.invoke_model()` with Bedrock request format
    - Implement `generate_structured_object()` using Claude's JSON mode via Bedrock
    - Implement `generate_image()` to raise `NotImplementedError` with clear message
    - Implement `generate_audio()` to raise `NotImplementedError` with clear message
    - Implement `search_recent_news()` to raise `NotImplementedError` with clear message
    - Add retry logic for AWS throttling errors
    - Add error conversion from Bedrock/boto3 exceptions to LLM exceptions
- [ ] Update `providers/factory.py`: Add Claude routing logic
  - Update `create_llm_provider()` to detect Claude models by name (starts with "claude-")
  - If model starts with "claude-", route to `AnthropicProvider` or `BedrockProvider` based on config
  - Update `get_available_providers()` to include `ANTHROPIC` and `BEDROCK`

### Backend: Tests

- [ ] Update `test_llm_services_unit.py`: Add Claude provider tests
  - Add unit tests for `estimate_claude_cost()` with all three models
  - Add unit tests for `convert_to_claude_messages()` message format conversion
  - Add unit tests for `parse_claude_response()` response parsing
  - Add unit tests for `get_claude_model_config()` model metadata
  - Add mock tests for `AnthropicProvider.generate_response()` using `AsyncMock`
  - Add mock tests for `AnthropicProvider.generate_structured_object()` using `AsyncMock`
  - Add tests for unsupported operations raising `NotImplementedError`
  - Add mock tests for `BedrockProvider.generate_response()` using `AsyncMock`
  - Add mock tests for `BedrockProvider.generate_structured_object()` using `AsyncMock`
  - Add tests for error handling and exception conversion
- [ ] Update `backend/tests/test_lesson_creation_integration.py`: Add model selection capability
  - Add environment variable or parameter to specify model for integration tests
  - Add ability to test lesson creation flow with Claude models
  - Ensure integration tests work with both OpenAI and Claude models

### Backend: Dependencies

- [ ] Update `backend/requirements.txt`: Add new dependencies
  - Add `anthropic>=0.34.0` for Anthropic Direct API support
  - Add `boto3>=1.34.0` for AWS Bedrock support (optional but recommended)

### Backend: Database Migration

- [ ] No migration needed - existing `llm_requests` table already supports new provider/model values

### Verification Tasks

- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/add-claude-support/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Environment Variables

### Anthropic Direct API

```bash
# Required for Anthropic Direct API
ANTHROPIC_API_KEY=sk-ant-...

# Optional: specify default Claude model
ANTHROPIC_MODEL=claude-haiku-4-5

# Provider selection (auto-detected if not specified)
LLM_PROVIDER=anthropic
```

### AWS Bedrock

```bash
# Required for AWS Bedrock
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-west-2

# Optional: specify Bedrock model ID
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Provider selection (auto-detected if not specified)
LLM_PROVIDER=bedrock
```

### Model Name Mapping

The system will map friendly model names to provider-specific IDs:

**Anthropic Direct API:**
- `claude-sonnet-4-5` → `claude-sonnet-4-5-20250514`
- `claude-haiku-4-5` → `claude-haiku-4-5-20250219`
- `claude-opus-4-1` → `claude-opus-4-1-20250115`

**AWS Bedrock:**
- `claude-sonnet-4-5` → `anthropic.claude-sonnet-4-5-v1:0`
- `claude-haiku-4-5` → `anthropic.claude-haiku-4-5-v1:0`
- `claude-opus-4-1` → `anthropic.claude-opus-4-1-v1:0`

(Note: Exact Bedrock model IDs may need adjustment based on AWS availability)

---

## Technical Notes

### Provider Selection Logic

The factory determines provider based on model name:
1. If model starts with `gpt-`, route to `OpenAIProvider`
2. If model starts with `claude-`, route to Claude provider:
   - If `ANTHROPIC_API_KEY` is set → `AnthropicProvider`
   - If AWS credentials are set → `BedrockProvider`
   - If neither is configured → raise configuration error

### Error Handling

Claude-specific errors should be converted to standard LLM exceptions:
- Anthropic `AuthenticationError` → `LLMAuthenticationError`
- Anthropic `RateLimitError` → `LLMRateLimitError`
- Anthropic `APIError` → `LLMError`
- Bedrock throttling → `LLMRateLimitError`
- Bedrock validation errors → `LLMValidationError`

### Structured Outputs

Claude supports structured outputs via:
- System prompt instructing JSON format
- Response parsing and validation against Pydantic model
- Retry logic if parsing fails (up to max retries)

### Testing Strategy

**Unit Tests:**
- Mock Anthropic SDK calls using `AsyncMock`
- Mock boto3 Bedrock calls using `AsyncMock`
- Test cost calculation with known token counts
- Test message format conversion
- Test error handling and retries

**Integration Tests:**
- Allow specifying model via environment variable
- Test with real Claude API (if credentials available)
- Fall back to OpenAI if Claude not configured
- Validate full request/response cycle including DB logging

### Dependencies

**New Python packages required:**
```
anthropic>=0.34.0  # Anthropic Python SDK
boto3>=1.34.0      # AWS SDK (if using Bedrock)
```

Add to `backend/requirements.txt`.

---

## Notes

- No changes to public interfaces - provider abstraction handles everything
- No database migrations needed - existing schema supports new providers
- No frontend changes needed - model names displayed automatically
- Existing OpenAI functionality remains unchanged
- Modules that use LLM services (`flow_engine`, `conversation_engine`, `content_creator`, `learning_coach`) can immediately use Claude models by specifying model name
