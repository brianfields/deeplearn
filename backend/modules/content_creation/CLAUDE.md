# Content Creation Module

## Purpose
This module handles the creation, authoring, and management of educational content including topics, learning components (MCQs, didactic snippets, socratic dialogues), and refined material extraction from source content.

## Domain Responsibility
**"Creating and managing educational content"**

The Content Creation module owns all aspects of content authoring:
- Extracting structured material from unstructured source content
- Generating learning components (MCQs, didactic snippets, glossaries, socratic dialogues)
- Managing topic lifecycle (creation, editing, validation, deletion)
- Content quality validation and improvement
- LLM-powered content generation workflows

## Architecture

### Module API (Public Interface)
```python
# module_api/content_creation_service.py
class ContentCreationService:
    @staticmethod
    def create_topic_from_source(source_material: str, domain: str) -> Topic:
        """Create a topic with refined material from unstructured source"""

    @staticmethod
    def get_topic(topic_id: str) -> Topic:
        """Get topic by ID for other modules to consume"""

    @staticmethod
    def generate_components(topic_id: str, component_types: List[str]) -> List[Component]:
        """Generate learning components for a topic"""

    @staticmethod
    def validate_topic_structure(topic: Topic) -> ValidationResult:
        """Validate topic meets quality standards"""

# module_api/types.py
@dataclass
class Topic:
    id: str
    title: str
    description: str
    learning_objectives: List[str]
    components: List[Component]

@dataclass
class Component:
    id: str
    type: ComponentType  # mcq, didactic_snippet, socratic_dialogue, etc.
    content: Dict[str, Any]
    learning_objective: str
```

### HTTP API (Frontend Interface)
```python
# http_api/routes.py
@router.post("/api/content/topics")
async def create_topic(request: CreateTopicRequest) -> TopicResponse:
    """Create topic from source material"""

@router.get("/api/content/topics/{topic_id}")
async def get_topic(topic_id: str) -> TopicDetailResponse:
    """Get topic with components for editing"""

@router.post("/api/content/topics/{topic_id}/components")
async def create_component(topic_id: str, request: CreateComponentRequest) -> ComponentResponse:
    """Generate component for topic"""

@router.delete("/api/content/topics/{topic_id}")
async def delete_topic(topic_id: str) -> None:
    """Delete topic and all components"""
```

### Domain Layer (Business Logic)
```python
# domain/entities/topic.py
class Topic:
    def add_component(self, component: Component) -> None:
        """Business logic for adding components to topic"""
        if not self._can_add_component(component):
            raise InvalidComponentError()
        self.components.append(component)

    def validate_structure(self) -> bool:
        """Business rules for topic validation"""
        return (
            len(self.learning_objectives) >= 2 and
            len(self.components) >= 1 and
            self._has_required_component_types()
        )

# domain/policies/content_validation_policy.py
class ContentValidationPolicy:
    @staticmethod
    def validate_mcq_quality(mcq: MCQComponent) -> ValidationResult:
        """Business rules for MCQ quality validation"""

    @staticmethod
    def validate_learning_objectives(objectives: List[str]) -> bool:
        """Business rules for learning objective validation"""
```

### Infrastructure Layer (Technical Implementation)
```python
# infrastructure/repositories/topic_repository.py
class TopicRepository:
    @staticmethod
    def save(topic: Topic) -> Topic:
        """Persist topic to database"""

    @staticmethod
    def get_by_id(topic_id: str) -> Optional[Topic]:
        """Retrieve topic from database"""

# infrastructure/llm_adapters/mcq_generator.py
class MCQGenerator:
    def generate_mcqs(self, refined_material: RefinedMaterial) -> List[MCQComponent]:
        """Generate MCQs using LLM service"""
```

## Cross-Module Communication

### Provides to Other Modules
- **Topic Catalog Module**: Topic metadata for browsing
- **Learning Session Module**: Topic content and components for learning
- **Learning Analytics Module**: Topic structure for progress calculation

### Dependencies
- **Infrastructure Module**: Database service, LLM service, configuration

### Communication Examples
```python
# Other modules access via module_api only
from modules.content_creation.module_api import ContentCreationService, Topic

# Learning Session module getting topic content
topic = ContentCreationService.get_topic(topic_id)
components = topic.components

# Topic Catalog module getting topic metadata
topics = ContentCreationService.get_all_topics()
```

## Key Business Rules

1. **Topic Structure**: Every topic must have at least 2 learning objectives and 1 component
2. **Component Quality**: MCQs must have 4 choices with clear correct answer and justifications
3. **Content Validation**: All generated content must pass quality validation before saving
4. **Learning Objective Alignment**: Each component must align with at least one learning objective
5. **Source Material Processing**: Refined material extraction must preserve key concepts and learning goals

## Data Flow

1. **Content Creation Workflow**:
   ```
   Source Material → Refined Material Extraction → Topic Creation → Component Generation → Quality Validation → Storage
   ```

2. **Content Consumption Workflow**:
   ```
   Topic Request → Repository Lookup → Domain Entity Mapping → API Response
   ```

## Testing Strategy

### Domain Tests (Pure Business Logic)
```python
def test_topic_validation():
    topic = Topic(title="Test", objectives=["Learn X", "Understand Y"])
    assert topic.validate_structure() == True

def test_component_addition_rules():
    topic = Topic(title="Test")
    mcq = MCQComponent(question="What is X?", choices=["A", "B", "C", "D"])
    topic.add_component(mcq)
    assert len(topic.components) == 1
```

### Service Tests (Orchestration)
```python
@patch('infrastructure.repositories.TopicRepository')
@patch('infrastructure.llm_adapters.MCQGenerator')
def test_create_topic_from_source(mock_repo, mock_generator):
    # Test service orchestration without business logic
    result = ContentCreationService.create_topic_from_source("source", "domain")
    mock_repo.save.assert_called_once()
```

### HTTP Tests (API Endpoints)
```python
def test_create_topic_endpoint():
    response = client.post("/api/content/topics", json={"source": "test", "domain": "math"})
    assert response.status_code == 201
    assert "topic_id" in response.json()
```

## Anti-Patterns to Avoid

❌ **Business logic in HTTP routes**
❌ **Business logic in service layer**
❌ **Direct database access from domain**
❌ **LLM calls from domain entities**
❌ **Cross-module imports from internal directories**

## Module Evolution

This module can be extended with:
- **Content Templates**: Reusable content templates
- **Collaborative Editing**: Multi-user content creation
- **Content Versioning**: Track content changes over time
- **Advanced Validation**: AI-powered content quality assessment
- **Content Analytics**: Usage analytics for created content

The modular architecture ensures these features can be added without affecting other modules.
