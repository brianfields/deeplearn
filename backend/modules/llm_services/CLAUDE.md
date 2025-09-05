# LLM Services Module

## Purpose
This module provides language model integration and prompt management services to all other modules. It handles LLM client management, prompt templating, response processing, and AI-powered content generation without containing any business domain logic.

## Domain Responsibility
**"Language model integration and prompt management services"**

The LLM Services module owns all aspects of LLM integration:
- LLM provider client management (OpenAI, Azure, etc.)
- Prompt template management and rendering
- Response processing and validation
- Usage tracking and rate limiting
- Model configuration and switching
- AI safety and content filtering

## Architecture

### Module API (Public Interface)
```python
# module_api/llm_service.py
class LLMService:
    @staticmethod
    def generate_content(prompt_name: str, context: Dict[str, Any]) -> LLMResponse:
        """Generate content using specified prompt template"""

    @staticmethod
    def generate_mcq(material: str, learning_objective: str) -> MCQResponse:
        """Generate multiple choice question from material"""

    @staticmethod
    def extract_refined_material(source_material: str, domain: str) -> RefinedMaterialResponse:
        """Extract and refine learning material from source content"""

    @staticmethod
    def generate_didactic_snippet(concept: str, context: str) -> DidacticResponse:
        """Generate educational explanation snippet"""

    @staticmethod
    def validate_prompt_context(prompt_name: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate context matches prompt requirements"""

# module_api/types.py
@dataclass
class LLMResponse:
    content: str
    metadata: Dict[str, Any]
    usage_stats: UsageStats
    provider: str
    model: str

@dataclass
class MCQResponse:
    question: str
    choices: Dict[str, str]
    correct_answer: str
    justifications: Dict[str, str]
    difficulty: int

@dataclass
class RefinedMaterialResponse:
    title: str
    learning_objectives: List[str]
    key_concepts: List[str]
    structured_content: str

@dataclass
class UsageStats:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimate: float
```

### Domain Layer (LLM Logic)
```python
# domain/entities/prompt.py
class Prompt:
    def __init__(self, name: str, template: str, variables: List[str]):
        self.name = name
        self.template = template
        self.variables = variables
        self.metadata = {}

    def render(self, context: Dict[str, Any]) -> str:
        """Business logic for prompt rendering with context validation"""
        if not self.validate_context(context):
            raise InvalidPromptContextError(f"Missing required variables: {self.get_missing_variables(context)}")

        return self.template.format(**context)

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Business rules for context validation"""
        return all(var in context for var in self.variables)

    def get_missing_variables(self, context: Dict[str, Any]) -> List[str]:
        """Business logic for identifying missing context variables"""
        return [var for var in self.variables if var not in context]

# domain/entities/llm_provider.py
class LLMProvider:
    def __init__(self, provider_type: str, config: LLMConfig):
        self.provider_type = provider_type
        self.config = config
        self.client = None

    def generate_response(self, prompt: Prompt, context: Dict[str, Any]) -> LLMResponse:
        """Business logic for LLM response generation"""
        rendered_prompt = prompt.render(context)

        if not self.is_available():
            raise LLMProviderUnavailableError(f"Provider {self.provider_type} is not available")

        raw_response = self.client.generate(rendered_prompt, self.config.parameters)

        return LLMResponse(
            content=raw_response.content,
            metadata=self.extract_metadata(raw_response),
            usage_stats=self.calculate_usage_stats(raw_response),
            provider=self.provider_type,
            model=self.config.model
        )

    def is_available(self) -> bool:
        """Business logic for provider availability check"""
        return self.client is not None and self.client.is_healthy()

# domain/policies/content_safety_policy.py
class ContentSafetyPolicy:
    @staticmethod
    def validate_generated_content(content: str, content_type: str) -> SafetyResult:
        """Business rules for content safety validation"""

    @staticmethod
    def filter_inappropriate_content(content: str) -> str:
        """Business rules for content filtering"""

    @staticmethod
    def validate_educational_appropriateness(content: str) -> bool:
        """Business rules for educational content validation"""
```

### Infrastructure Layer (Technical Implementation)
```python
# infrastructure/clients/openai_client.py
class OpenAIClient:
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def generate(self, prompt: str, parameters: Dict[str, Any]) -> RawLLMResponse:
        """OpenAI-specific implementation"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            **parameters
        )

        return RawLLMResponse(
            content=response.choices[0].message.content,
            raw_response=response,
            provider_metadata={"model": self.config.model}
        )

    def is_healthy(self) -> bool:
        """Check if OpenAI service is available"""
        try:
            self.client.models.list()
            return True
        except Exception:
            return False

# infrastructure/repositories/prompt_repository.py
class PromptRepository:
    @staticmethod
    def get_by_name(name: str) -> Optional[Prompt]:
        """Retrieve prompt template by name"""

    @staticmethod
    def save(prompt: Prompt) -> Prompt:
        """Save prompt template"""

    @staticmethod
    def get_all_by_category(category: str) -> List[Prompt]:
        """Get all prompts in a category"""

# infrastructure/adapters/usage_tracker.py
class UsageTracker:
    def track_usage(self, response: LLMResponse) -> None:
        """Track LLM usage for billing and monitoring"""

    def get_usage_stats(self, time_period: str) -> UsageReport:
        """Get usage statistics for reporting"""

    def check_rate_limits(self, provider: str) -> RateLimitStatus:
        """Check current rate limit status"""
```

### HTTP API (Management Interface)
```python
# http_api/routes.py
@router.get("/api/llm/prompts")
async def list_prompts(category: Optional[str] = None) -> PromptsResponse:
    """List available prompt templates"""

@router.post("/api/llm/prompts")
async def create_prompt(request: CreatePromptRequest) -> PromptResponse:
    """Create new prompt template"""

@router.get("/api/llm/usage")
async def get_usage_stats(period: str = "day") -> UsageStatsResponse:
    """Get LLM usage statistics"""

@router.post("/api/llm/test")
async def test_prompt(request: TestPromptRequest) -> TestResponse:
    """Test prompt with sample context"""
```

## Cross-Module Communication

### Provides to Other Modules
- **Content Creation Module**: MCQ generation, material extraction, content creation
- **All Modules**: General purpose LLM content generation

### Dependencies
- **Infrastructure Module**: Configuration, logging, database for prompt storage

### Communication Examples
```python
# Content Creation module using LLM services
from modules.llm_services.module_api import LLMService

# Generate MCQ from material
mcq_response = LLMService.generate_mcq(
    material="Python is a programming language...",
    learning_objective="Understand Python basics"
)

# Extract refined material
refined_response = LLMService.extract_refined_material(
    source_material=raw_content,
    domain="computer_science"
)

# Generate didactic snippet
snippet_response = LLMService.generate_didactic_snippet(
    concept="recursion",
    context="beginner programming course"
)
```

## Key Business Rules

1. **Prompt Validation**: All prompts must have required variables validated before rendering
2. **Content Safety**: All generated content must pass safety and appropriateness checks
3. **Usage Tracking**: All LLM calls must be tracked for billing and monitoring
4. **Rate Limiting**: Respect provider rate limits and implement backoff strategies
5. **Model Selection**: Automatically select appropriate model based on task complexity
6. **Response Validation**: Validate LLM responses match expected format and content

## Data Flow

1. **Content Generation Workflow**:
   ```
   Request → Get Prompt Template → Validate Context → Render Prompt → Call LLM → Process Response → Return Result
   ```

2. **Prompt Management Workflow**:
   ```
   Create Prompt → Validate Template → Store in Repository → Make Available via API
   ```

3. **Usage Tracking Workflow**:
   ```
   LLM Call → Extract Usage Stats → Store Metrics → Update Rate Limits → Generate Reports
   ```

## Testing Strategy

### Domain Tests (Business Logic)
```python
def test_prompt_rendering():
    prompt = Prompt("test", "Hello {name}!", ["name"])
    context = {"name": "World"}

    result = prompt.render(context)
    assert result == "Hello World!"

def test_prompt_validation():
    prompt = Prompt("test", "Hello {name}!", ["name"])
    context = {"age": 25}  # Missing 'name'

    assert prompt.validate_context(context) == False
    assert "name" in prompt.get_missing_variables(context)

def test_content_safety_validation():
    content = "This is appropriate educational content"
    result = ContentSafetyPolicy.validate_generated_content(content, "mcq")

    assert result.is_safe == True
```

### Service Tests (Orchestration)
```python
@patch('infrastructure.clients.OpenAIClient')
@patch('infrastructure.repositories.PromptRepository')
def test_generate_content(mock_repo, mock_client):
    mock_prompt = Prompt("test", "Generate: {topic}", ["topic"])
    mock_repo.get_by_name.return_value = mock_prompt

    result = LLMService.generate_content("test", {"topic": "Python"})

    mock_repo.get_by_name.assert_called_once_with("test")
    assert result.content is not None
```

### Integration Tests (LLM Providers)
```python
def test_openai_integration():
    """Test actual OpenAI API integration"""
    client = OpenAIClient(test_config)
    response = client.generate("Hello, world!", {})

    assert len(response.content) > 0
    assert response.provider_metadata["model"] is not None
```

## Prompt Templates

### MCQ Generation
```python
MCQ_PROMPT = """
Generate a multiple choice question based on the following material:

Material: {material}
Learning Objective: {learning_objective}

Requirements:
- Create 1 question with 4 choices (A, B, C, D)
- Mark the correct answer
- Provide justifications for each choice
- Ensure question tests understanding of the learning objective

Format your response as JSON:
{
  "question": "...",
  "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct_answer": "B",
  "justifications": {"A": "...", "B": "...", "C": "...", "D": "..."}
}
"""
```

### Material Extraction
```python
MATERIAL_EXTRACTION_PROMPT = """
Extract and structure learning material from the following source content:

Source Material: {source_material}
Domain: {domain}

Extract:
1. A clear title for the learning topic
2. 3-5 specific learning objectives
3. Key concepts and definitions
4. Structured content organized for learning

Format as JSON:
{
  "title": "...",
  "learning_objectives": ["...", "..."],
  "key_concepts": ["...", "..."],
  "structured_content": "..."
}
"""
```

## Performance Considerations

### LLM Optimization
- **Prompt Caching**: Cache rendered prompts to avoid re-processing
- **Response Caching**: Cache LLM responses for identical prompts
- **Batch Processing**: Batch multiple requests when possible
- **Model Selection**: Use appropriate model size for task complexity

### Rate Limiting
- **Provider Limits**: Respect OpenAI/Azure rate limits
- **Exponential Backoff**: Implement retry with backoff on rate limit errors
- **Queue Management**: Queue requests during high load periods

## Anti-Patterns to Avoid

❌ **Business domain logic in LLM module**
❌ **Direct LLM client access from other modules**
❌ **Hardcoded prompts in business logic**
❌ **Untracked LLM usage**
❌ **Missing content safety validation**

## Security Considerations

- **API Key Management**: Secure storage and rotation of LLM provider API keys
- **Content Filtering**: Filter inappropriate or harmful generated content
- **Usage Monitoring**: Monitor for unusual usage patterns
- **Input Sanitization**: Sanitize user inputs before including in prompts

## Module Evolution

This module can be extended with:
- **Multiple LLM Providers**: Support for Anthropic, Google, local models
- **Advanced Prompt Engineering**: Chain-of-thought, few-shot learning
- **Custom Model Fine-tuning**: Domain-specific model training
- **Advanced Safety**: AI alignment and safety measures
- **Prompt Optimization**: Automatic prompt optimization and A/B testing

The modular architecture ensures LLM capabilities can be enhanced without affecting business logic in other modules.
