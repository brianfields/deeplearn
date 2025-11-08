# OpenRouter LLM Service Provider - Implementation Spec

## User Story

**As a** developer using the LLM services module,

**I want** to add OpenRouter as a supported LLM provider,

**So that** I can access OpenRouter's unified API endpoint with 200+ models from multiple providers using a single API key and consistent interface.

### User Experience Changes

**Backend (Service Layer):**
- Developers can specify OpenRouter models using the format `openrouter/provider/model` (e.g., `openrouter/anthropic/claude-3-opus`, `openrouter/openai/gpt-4`)
- The system automatically routes these requests to the OpenRouter provider
- All existing LLM service methods work transparently with OpenRouter models:
  - `generate_response()` for text generation
  - `generate_structured_response()` for structured outputs with Pydantic models
- OpenRouter-specific cost tracking is captured from API responses
- Token usage (input/output) and caching stats are recorded in the database

**Configuration:**
- Set `OPENROUTER_API_KEY` environment variable to enable OpenRouter
- Optionally set `OPENROUTER_BASE_URL` (defaults to `https://openrouter.ai/api/v1`)

**Developer Experience:**
```python
# Existing pattern, now works with OpenRouter
llm = llm_services_provider(session)

# Use OpenRouter model with automatic routing
response, request_id = await llm.generate_response(
    messages=[LLMMessage(role="user", content="Hello!")],
    model="openrouter/anthropic/claude-3-opus"
)

# Structured output also works
result, request_id, usage = await llm.generate_structured_response(
    messages=[...],
    response_model=MyPydanticModel,
    model="openrouter/openai/gpt-4"
)
```

### What's NOT Changing
- No frontend (admin/mobile) changes - this is backend infrastructure only
- No new routes or public API methods - uses existing `llm_services` interface
- Other providers (OpenAI, Anthropic, Gemini, Bedrock) remain unchanged
- Existing consumers of `llm_services` require no code changes

---

## Requirements Summary

### Functional Requirements

1. **Provider Implementation**
   - Create `OpenRouterProvider` class that extends `LLMProvider` base class
   - Implement text generation via OpenRouter's unified API endpoint
   - Implement structured output generation using Pydantic models
   - Support OpenRouter's model naming format: `openrouter/provider/model`

2. **Configuration**
   - Add OpenRouter configuration fields to `LLMConfig`
   - Read `OPENROUTER_API_KEY` and `OPENROUTER_BASE_URL` from environment
   - Validate OpenRouter configuration when provider is selected

3. **Model Routing**
   - Automatically route models with `openrouter/` prefix to OpenRouter provider
   - Preserve existing explicit whitelist (`MODEL_PROVIDER_MAP`) for other providers
   - Fail explicitly if OpenRouter is not configured when an OpenRouter model is requested

4. **Cost & Usage Tracking**
   - Parse OpenRouter API response for cost information
   - Extract input/output token counts from response
   - Record caching statistics if provided by OpenRouter
   - Store all data in existing `llm_requests` table

5. **Error Handling**
   - Handle OpenRouter-specific authentication errors
   - Handle rate limiting errors
   - Handle invalid model errors
   - Provide clear error messages for configuration issues

6. **Not Implemented (Future)**
   - Image generation (`generate_image()` - raise `NotImplementedError`)
   - Audio generation (`generate_audio()` - raise `NotImplementedError`)
   - Web search (`search_recent_news()` - raise `NotImplementedError`)

### Non-Functional Requirements

1. **Architecture Compliance**
   - Follow existing provider pattern (extend `LLMProvider`)
   - Maintain DTO discipline (use internal types, convert at boundaries)
   - No ORM leakage (repo returns ORM, service returns DTOs)
   - Keep changes within `llm_services` module

2. **Testing**
   - Unit tests with mocked HTTP responses (no real API calls)
   - Test success cases for text and structured generation
   - Test error handling for authentication, rate limits, invalid models
   - Test cost/token parsing from OpenRouter responses

3. **Code Quality**
   - Explicit return types on all functions
   - Follow existing naming conventions
   - Comprehensive docstrings
   - Type hints throughout

### Constraints

- No database migrations (existing schema sufficient)
- No new public APIs (uses existing `LLMServicesProvider` interface)
- No frontend changes (backend infrastructure only)
- Must work alongside existing providers without conflicts

### Acceptance Criteria

- [ ] OpenRouter models can be used via `generate_response()` with `openrouter/` prefix
- [ ] Structured output generation works with OpenRouter models
- [ ] Cost and token usage are correctly extracted from OpenRouter responses
- [ ] Caching statistics are recorded when provided by OpenRouter
- [ ] Clear error messages when OpenRouter is not configured
- [ ] All unit tests pass with mocked responses
- [ ] Existing providers (OpenAI, Anthropic, Gemini, Bedrock) remain unaffected
- [ ] No changes needed in consuming modules (`content_creator`, `learning_coach`, etc.)

---

## Cross-Stack Implementation Mapping

### Backend Module: `llm_services` (MODIFY)

**Files to Modify:**

1. **`backend/modules/llm_services/types.py`**
   - Add `OPENROUTER = "openrouter"` to `LLMProviderType` enum

2. **`backend/modules/llm_services/config.py`**
   - Add fields to `LLMConfig`:
     - `openrouter_api_key: str | None = Field(default=None)`
     - `openrouter_base_url: str | None = Field(default=None)`
   - Update `create_llm_config_from_env()`:
     - Read `OPENROUTER_API_KEY` from environment
     - Read `OPENROUTER_BASE_URL` from environment (default: `https://openrouter.ai/api/v1`)
     - Add provider selection logic for OpenRouter (when `OPENROUTER_API_KEY` is present)
     - Add validation for OpenRouter configuration

3. **`backend/modules/llm_services/providers/openrouter.py`** ⭐ **NEW FILE**
   - Create `OpenRouterProvider` class extending `LLMProvider`
   - Implement `generate_response()`:
     - Make HTTP request to OpenRouter API
     - Parse response for content, tokens, cost, caching stats
     - Handle errors (auth, rate limit, invalid model)
     - Update LLM request record in database
   - Implement `generate_structured_response()`:
     - Use OpenRouter's JSON mode or function calling for structured output
     - Parse and validate response against Pydantic model
     - Extract usage/cost information
   - Implement unsupported methods (raise `NotImplementedError`):
     - `generate_image()`
     - `generate_audio()`
     - `search_recent_news()`
   - Add cost estimation helper (if OpenRouter provides pricing info)

4. **`backend/modules/llm_services/providers/factory.py`**
   - Import: `from .openrouter import OpenRouterProvider`
   - Add case in `create_llm_provider()`:
     ```python
     if config.provider == LLMProviderType.OPENROUTER:
         return OpenRouterProvider(config, db_session)
     ```
   - Add `LLMProviderType.OPENROUTER` to `get_available_providers()` return list

5. **`backend/modules/llm_services/service.py`**
   - Update `_select_provider()` method:
     - Add check before existing `MODEL_PROVIDER_MAP` lookup:
       ```python
       # Special handling for OpenRouter prefix
       if model and model.startswith("openrouter/"):
           return self._ensure_provider(LLMProviderType.OPENROUTER)
       ```
     - Add helpful error message if OpenRouter not configured
   - No changes to `MODEL_PROVIDER_MAP` (prefix routing handles OpenRouter)

6. **`backend/modules/llm_services/test_llm_services_unit.py`**
   - Add test class `TestOpenRouterProvider`:
     - `test_generate_response_success` - mock successful text generation
     - `test_generate_response_with_cost_tracking` - verify cost/token parsing
     - `test_generate_response_with_caching` - verify caching stats
     - `test_generate_structured_response_success` - mock structured output
     - `test_generate_response_authentication_error` - mock auth failure
     - `test_generate_response_rate_limit_error` - mock rate limit
     - `test_generate_response_invalid_model_error` - mock invalid model
     - `test_unsupported_features` - verify image/audio/search raise NotImplementedError
   - Add test for model routing:
     - `test_openrouter_prefix_routing` - verify `openrouter/` prefix routes to OpenRouter

**Files NOT Modified:**
- `models.py` - existing schema sufficient
- `repo.py` - existing methods handle OpenRouter
- `public.py` - no public interface changes
- `routes.py` - no new HTTP endpoints
- `cache.py` - existing caching logic works
- `exceptions.py` - existing exceptions sufficient

### Frontend Changes

**None** - This is backend infrastructure only.

### Database Changes

**None** - Existing `llm_requests` table schema is sufficient.

---

## Implementation Checklist

### Phase 1: Core Provider Implementation

- [ ] Add `OPENROUTER = "openrouter"` to `LLMProviderType` enum in `backend/modules/llm_services/types.py`
- [ ] Add OpenRouter configuration fields to `LLMConfig` in `backend/modules/llm_services/config.py`
- [ ] Update `create_llm_config_from_env()` in `backend/modules/llm_services/config.py` to read OpenRouter environment variables
- [ ] Create `backend/modules/llm_services/providers/openrouter.py` with `OpenRouterProvider` class skeleton
- [ ] Implement `OpenRouterProvider.__init__()` to setup HTTP client for OpenRouter API
- [ ] Implement `OpenRouterProvider.generate_response()` for text generation
- [ ] Implement `OpenRouterProvider.generate_structured_response()` for structured outputs
- [ ] Implement stub methods that raise `NotImplementedError`: `generate_image()`, `generate_audio()`, `search_recent_news()`
- [ ] Add OpenRouter response parsing logic for cost, tokens, and caching stats
- [ ] Update `backend/modules/llm_services/providers/factory.py` to import and instantiate `OpenRouterProvider`
- [ ] Add `LLMProviderType.OPENROUTER` to `get_available_providers()` in factory
- [ ] Update `_select_provider()` in `backend/modules/llm_services/service.py` to handle `openrouter/` prefix
- [ ] Add error handling in `_select_provider()` for unconfigured OpenRouter provider

### Phase 2: Error Handling & Edge Cases & Testing

- [ ] Add OpenRouter-specific error handling (authentication, rate limits, invalid models)
- [ ] Add validation in `create_llm_config_from_env()` for OpenRouter configuration
- [ ] Ensure cost estimation works (or returns 0.0 if not available)
- [ ] Test with missing/invalid API keys
- [ ] Create unit tests for `OpenRouterProvider.generate_response()` with mocked responses
- [ ] Create unit tests for `OpenRouterProvider.generate_structured_response()` with mocked responses
- [ ] Ensure all mocks use `AsyncMock` for async methods

### Phase 3: Documentation & Validation

- [ ] Add docstrings to `OpenRouterProvider` class and all methods
- [ ] Add inline comments explaining OpenRouter-specific response parsing
- [ ] Update type hints to be explicit on all methods
- [ ] Document OpenRouter configuration in `config.py` docstrings
- [ ] Ensure lint passes, i.e. './format_code.sh --no-venv' runs clean
- [ ] Ensure backend unit tests pass, i.e. cd backend && scripts/run_unit.py
- [ ] Ensure integration tests pass, i.e. cd backend && scripts/run_integration.py runs clean
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/openrouter-llm-service-provider/trace.md
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code

---

## Technical Implementation Notes

### OpenRouter API Integration

**Endpoint:**
- Base URL: `https://openrouter.ai/api/v1` (configurable via `OPENROUTER_BASE_URL`)
- Text generation: `POST /chat/completions` (OpenAI-compatible format)

**Authentication:**
- Header: `Authorization: Bearer {OPENROUTER_API_KEY}`
- Optional: `HTTP-Referer` and `X-Title` headers for tracking

**Request Format (OpenAI-compatible):**
```json
{
  "model": "anthropic/claude-3-opus",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response Format:**
```json
{
  "id": "gen-123",
  "model": "anthropic/claude-3-opus",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "cost": 0.000123  // OpenRouter-specific field
}
```

**Model Naming:**
- Use format: `openrouter/{provider}/{model}`
- Examples:
  - `openrouter/anthropic/claude-3-opus`
  - `openrouter/openai/gpt-4`
  - `openrouter/meta-llama/llama-3-70b`
- The `openrouter/` prefix is stripped before sending to OpenRouter API

**Structured Output:**
- Use OpenRouter's JSON mode: `response_format: {"type": "json_object"}`
- Include Pydantic schema in system message
- Parse and validate response against Pydantic model

**Cost Tracking:**
- OpenRouter returns cost in `cost` field (USD)
- Store in `LLMRequestModel.cost_estimate`
- Fall back to 0.0 if not provided

**Caching:**
- OpenRouter may provide caching stats in `usage` object
- Check for fields like `cache_hit`, `cached_tokens`
- Store in `LLMRequestModel.cached` and related fields

### Error Handling

**Authentication Errors (401):**
- Raise `LLMAuthenticationError` with message about `OPENROUTER_API_KEY`

**Rate Limit Errors (429):**
- Raise `LLMRateLimitError` with retry-after information if available

**Invalid Model Errors (400/404):**
- Raise `LLMError` with message about unsupported model

**Timeout Errors:**
- Raise `LLMTimeoutError` with information about request timeout

### Testing Strategy

**Mock OpenRouter Responses:**
```python
mock_response = {
    "id": "gen-test-123",
    "model": "anthropic/claude-3-opus",
    "choices": [{
        "message": {
            "role": "assistant",
            "content": "Test response"
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    },
    "cost": 0.000123
}
```

**Use AsyncMock:**
```python
from unittest.mock import AsyncMock, patch

@patch('httpx.AsyncClient.post')
async def test_generate_response(mock_post):
    mock_post.return_value = AsyncMock(
        json=lambda: mock_response,
        status_code=200
    )
    # Test code...
```

### Architecture Compliance

**Provider Pattern:**
- Extend `LLMProvider` base class
- Implement abstract methods: `generate_response()`, `generate_image()`, etc.
- Use `_create_llm_request()`, `_update_llm_request_success()`, `_update_llm_request_error()` helpers

**DTO Discipline:**
- Convert OpenRouter API responses to internal types (`LLMResponse`, `LLMMessage`)
- Service layer converts internal types to DTOs for public interface
- No ORM objects cross module boundaries

**Configuration:**
- All OpenRouter config in `LLMConfig` (no module-level globals)
- Environment variables read only in `create_llm_config_from_env()`
- Validation in `LLMConfig.validate_config()`

**Error Handling:**
- Use existing exception hierarchy (`LLMError`, `LLMAuthenticationError`, etc.)
- Provide clear, actionable error messages
- No silent failures

---

## Out of Scope

The following are explicitly NOT part of this spec:

1. **Image Generation via OpenRouter** - Not implemented in this iteration
2. **Audio Generation via OpenRouter** - Not implemented in this iteration
3. **Web Search via OpenRouter** - Not implemented in this iteration
4. **Frontend Integration** - No admin dashboard or mobile app changes
5. **New Routes/Endpoints** - Uses existing `llm_services` public interface
6. **Database Schema Changes** - Existing schema is sufficient
7. **Deployment/Configuration Management** - Assumes environment variables are set externally
8. **Cost Optimization/Caching Strategy** - Uses existing caching infrastructure
9. **Model Discovery/Listing** - No automatic discovery of available OpenRouter models
10. **Rate Limiting Implementation** - Relies on OpenRouter's rate limiting
11. **Backward Compatibility** - Not a concern (pre-deployment application)

---

## Dependencies

**Python Packages:**
- `httpx` or `aiohttp` (already in use for HTTP requests)
- `pydantic` (already in use for DTOs/validation)
- `sqlalchemy` (already in use for database)

**External Services:**
- OpenRouter API (requires `OPENROUTER_API_KEY`)

**Internal Modules:**
- None (self-contained within `llm_services` module)

---

## Risks & Mitigations

**Risk 1: OpenRouter API format changes**
- **Mitigation:** Follow OpenAI-compatible format (stable); version response parsing

**Risk 2: Cost tracking unavailable**
- **Mitigation:** Gracefully handle missing `cost` field (default to 0.0)

**Risk 3: Model naming inconsistencies**
- **Mitigation:** Document expected format; provide clear error messages for invalid formats

**Risk 4: Structured output not supported by all models**
- **Mitigation:** Check model capabilities; return clear error if not supported

**Risk 5: Rate limiting without retry-after headers**
- **Mitigation:** Use exponential backoff; respect existing retry configuration

---

## Success Metrics

- [ ] OpenRouter provider successfully integrates with existing `llm_services` architecture
- [ ] All unit tests pass with mocked OpenRouter responses
- [ ] No regressions in existing providers (OpenAI, Anthropic, Gemini, Bedrock)
- [ ] Cost and token tracking works correctly for OpenRouter requests
- [ ] Clear error messages for configuration/authentication issues
- [ ] Code follows existing patterns and architecture guidelines
- [ ] No changes needed in consuming modules

---

## Future Enhancements (Not in This Spec)

1. **Image Generation Support** - Add OpenRouter image generation when available
2. **Audio Generation Support** - Add OpenRouter TTS when available
3. **Model Discovery** - Auto-fetch available models from OpenRouter API
4. **Cost Optimization** - Implement OpenRouter-specific caching strategies
5. **Provider Fallback** - Automatically fall back to alternative providers
6. **Model Aliases** - Support shorter aliases for common models
7. **Streaming Responses** - Support OpenRouter's streaming API
8. **Fine-tuned Models** - Support user's fine-tuned models on OpenRouter
