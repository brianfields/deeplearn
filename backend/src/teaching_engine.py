"""
Teaching Engine - Main loop for conversational learning
Implements simplified rule-based teaching strategy selection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from llm_interface import LLMProvider, LLMMessage, MessageRole

logger = logging.getLogger(__name__)

class LearningPhase(Enum):
    INTRODUCTION = "introduction"
    EXPLORATION = "exploration"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    CONSOLIDATION = "consolidation"

class TeachingStrategy(Enum):
    DIRECT_INSTRUCTION = "direct_instruction"
    SOCRATIC_INQUIRY = "socratic_inquiry"
    GUIDED_PRACTICE = "guided_practice"
    ASSESSMENT = "assessment"
    ENCOURAGEMENT = "encouragement"

@dataclass
class StudentPerformance:
    """Simple performance tracking for student model"""
    understanding_score: float = 0.5  # 0.0 to 1.0
    engagement_score: float = 0.5     # 0.0 to 1.0
    response_quality: float = 0.5     # 0.0 to 1.0
    confusion_level: float = 0.0      # 0.0 to 1.0
    total_interactions: int = 0
    correct_responses: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class StudentModel:
    """Simple student model based on performance history"""
    student_id: str
    performance_history: List[StudentPerformance] = field(default_factory=list)
    preferred_strategies: Dict[TeachingStrategy, float] = field(default_factory=dict)
    learning_velocity: float = 0.5  # How quickly they progress
    needs_encouragement: bool = False
    last_interaction: Optional[datetime] = None

    def get_current_performance(self) -> StudentPerformance:
        """Get current performance based on recent history"""
        if not self.performance_history:
            return StudentPerformance()

        # Weight recent performance more heavily
        recent = self.performance_history[-3:]  # Last 3 interactions
        weights = [0.5, 0.3, 0.2] if len(recent) == 3 else [1.0] * len(recent)

        avg_understanding = sum(p.understanding_score * w for p, w in zip(recent, weights))
        avg_engagement = sum(p.engagement_score * w for p, w in zip(recent, weights))
        avg_response_quality = sum(p.response_quality * w for p, w in zip(recent, weights))
        avg_confusion = sum(p.confusion_level * w for p, w in zip(recent, weights))

        return StudentPerformance(
            understanding_score=avg_understanding,
            engagement_score=avg_engagement,
            response_quality=avg_response_quality,
            confusion_level=avg_confusion,
            total_interactions=sum(p.total_interactions for p in self.performance_history),
            correct_responses=sum(p.correct_responses for p in self.performance_history)
        )

@dataclass
class TopicMetadata:
    """Metadata about topics that influences teaching strategy"""
    topic_id: str
    topic_name: str
    difficulty_level: int = 1  # 1-5 scale
    recommended_strategies: List[TeachingStrategy] = field(default_factory=list)
    requires_visual_aids: bool = False
    prerequisite_topics: List[str] = field(default_factory=list)
    common_misconceptions: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 15

@dataclass
class LearningSession:
    """Current learning session state"""
    session_id: str
    student_id: str
    topic_id: str
    current_phase: LearningPhase = LearningPhase.INTRODUCTION
    start_time: datetime = field(default_factory=datetime.utcnow)
    phase_start_time: datetime = field(default_factory=datetime.utcnow)
    interaction_count: int = 0
    current_difficulty: float = 0.5
    objectives_covered: List[str] = field(default_factory=list)

    def time_in_current_phase(self) -> timedelta:
        return datetime.utcnow() - self.phase_start_time

    def total_session_time(self) -> timedelta:
        return datetime.utcnow() - self.start_time

@dataclass
class InteractionAnalysis:
    """Simple analysis of student interaction"""
    understanding_indicators: float  # 0.0 to 1.0
    engagement_indicators: float     # 0.0 to 1.0
    confusion_indicators: float      # 0.0 to 1.0
    response_length: int
    contains_question: bool
    positive_sentiment: bool

@dataclass
class StrategyDecision:
    """Decision about which teaching strategy to use"""
    strategy: TeachingStrategy
    confidence: float
    reasoning: str
    phase_recommendation: Optional[LearningPhase] = None

@dataclass
class TeachingResponse:
    """Response from the teaching engine"""
    content: str
    strategy_used: TeachingStrategy
    phase_used: LearningPhase
    next_recommendations: List[str]

class TeachingEngine:
    """Main teaching engine that orchestrates the learning process"""

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.student_models: Dict[str, StudentModel] = {}
        self.sessions: Dict[str, LearningSession] = {}
        self.topic_metadata: Dict[str, TopicMetadata] = {}

    async def process_student_interaction(self,
                                        message: str,
                                        session_id: str) -> TeachingResponse:
        """
        Main loop: Student message → AI teaching response
        """
        logger.info(f"Processing interaction for session {session_id}")

        # 1. Load current state
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        student_model = self.student_models.get(session.student_id)
        if not student_model:
            student_model = StudentModel(student_id=session.student_id)
            self.student_models[session.student_id] = student_model

        topic_metadata = self.topic_metadata.get(session.topic_id)

        # 2. Analyze student input (simple rule-based)
        interaction_analysis = await self._analyze_student_input(message, session)

        # 3. Update student model
        self._update_student_model(student_model, interaction_analysis, session)

        # 4. Determine teaching strategy
        strategy_decision = await self._select_teaching_strategy(
            session, student_model, topic_metadata, interaction_analysis
        )

        # 5. Generate AI response
        ai_response = await self._generate_teaching_response(
            strategy_decision, session, student_model, topic_metadata, message
        )

        # 6. Update session state
        self._update_session_state(session, strategy_decision, interaction_analysis)

        return ai_response

    async def _analyze_student_input(self,
                                   message: str,
                                   session: LearningSession) -> InteractionAnalysis:
        """Simple rule-based analysis of student input"""

        # Simple heuristics for analysis
        message_lower = message.lower()

        # Understanding indicators
        understanding_keywords = ['understand', 'got it', 'makes sense', 'clear', 'yes', 'right']
        confusion_keywords = ['confused', 'lost', 'unclear', 'don\'t understand', 'what', 'huh']

        understanding_score = 0.5
        for keyword in understanding_keywords:
            if keyword in message_lower:
                understanding_score += 0.2

        confusion_score = 0.0
        for keyword in confusion_keywords:
            if keyword in message_lower:
                confusion_score += 0.3
                understanding_score -= 0.2

        # Engagement indicators
        engagement_score = 0.5
        if len(message) > 50:  # Longer responses indicate engagement
            engagement_score += 0.2
        if '?' in message:  # Questions indicate engagement
            engagement_score += 0.1
        if any(word in message_lower for word in ['interesting', 'cool', 'wow', 'great']):
            engagement_score += 0.2

        # Clamp scores to valid range
        understanding_score = max(0.0, min(1.0, understanding_score))
        engagement_score = max(0.0, min(1.0, engagement_score))
        confusion_score = max(0.0, min(1.0, confusion_score))

        return InteractionAnalysis(
            understanding_indicators=understanding_score,
            engagement_indicators=engagement_score,
            confusion_indicators=confusion_score,
            response_length=len(message),
            contains_question='?' in message,
            positive_sentiment=any(word in message_lower for word in ['good', 'great', 'love', 'like', 'awesome'])
        )

    def _update_student_model(self,
                            student_model: StudentModel,
                            analysis: InteractionAnalysis,
                            session: LearningSession):
        """Update student model based on interaction analysis"""

        # Create new performance record
        performance = StudentPerformance(
            understanding_score=analysis.understanding_indicators,
            engagement_score=analysis.engagement_indicators,
            response_quality=min(1.0, analysis.response_length / 100.0),  # Normalize by length
            confusion_level=analysis.confusion_indicators,
            total_interactions=1,
            correct_responses=1 if analysis.understanding_indicators > 0.6 else 0
        )

        student_model.performance_history.append(performance)

        # Keep only last 20 interactions
        if len(student_model.performance_history) > 20:
            student_model.performance_history = student_model.performance_history[-20:]

        # Update learning velocity based on progress
        if len(student_model.performance_history) > 1:
            recent_avg = sum(p.understanding_score for p in student_model.performance_history[-3:]) / 3
            older_avg = sum(p.understanding_score for p in student_model.performance_history[-6:-3]) / 3 if len(student_model.performance_history) > 5 else 0.5
            student_model.learning_velocity = recent_avg - older_avg

        # Determine if needs encouragement
        recent_performance = student_model.get_current_performance()
        student_model.needs_encouragement = (
            recent_performance.understanding_score < 0.4 or
            recent_performance.engagement_score < 0.3 or
            recent_performance.confusion_level > 0.6
        )

        student_model.last_interaction = datetime.utcnow()

    async def _select_teaching_strategy(self,
                                      session: LearningSession,
                                      student_model: StudentModel,
                                      topic_metadata: Optional[TopicMetadata],
                                      analysis: InteractionAnalysis) -> StrategyDecision:
        """Rule-based teaching strategy selection"""

        current_performance = student_model.get_current_performance()

        # Rule 1: If student is confused, use direct instruction
        if analysis.confusion_indicators > 0.6:
            return StrategyDecision(
                strategy=TeachingStrategy.DIRECT_INSTRUCTION,
                confidence=0.9,
                reasoning="Student showing confusion - switching to direct instruction"
            )

        # Rule 2: If student needs encouragement, provide encouragement
        if student_model.needs_encouragement:
            return StrategyDecision(
                strategy=TeachingStrategy.ENCOURAGEMENT,
                confidence=0.8,
                reasoning="Student performance indicates need for encouragement"
            )

        # Rule 3: Use topic metadata recommendations if available
        if topic_metadata and topic_metadata.recommended_strategies:
            # Choose based on current phase and student performance
            for strategy in topic_metadata.recommended_strategies:
                if self._is_strategy_appropriate(strategy, session, current_performance):
                    return StrategyDecision(
                        strategy=strategy,
                        confidence=0.7,
                        reasoning=f"Using topic-recommended strategy: {strategy.value}"
                    )

        # Rule 4: Phase-based strategy selection
        phase_strategies = {
            LearningPhase.INTRODUCTION: [TeachingStrategy.DIRECT_INSTRUCTION, TeachingStrategy.SOCRATIC_INQUIRY],
            LearningPhase.EXPLORATION: [TeachingStrategy.SOCRATIC_INQUIRY, TeachingStrategy.GUIDED_PRACTICE],
            LearningPhase.PRACTICE: [TeachingStrategy.GUIDED_PRACTICE, TeachingStrategy.SOCRATIC_INQUIRY],
            LearningPhase.ASSESSMENT: [TeachingStrategy.ASSESSMENT],
            LearningPhase.CONSOLIDATION: [TeachingStrategy.SOCRATIC_INQUIRY, TeachingStrategy.DIRECT_INSTRUCTION]
        }

        available_strategies = phase_strategies.get(session.current_phase, [TeachingStrategy.SOCRATIC_INQUIRY])

        # Rule 5: Performance-based selection within phase
        if current_performance.understanding_score < 0.4:
            # Low understanding - prefer direct instruction
            preferred = TeachingStrategy.DIRECT_INSTRUCTION
        elif current_performance.engagement_score > 0.7:
            # High engagement - use Socratic inquiry
            preferred = TeachingStrategy.SOCRATIC_INQUIRY
        else:
            # Moderate - use guided practice
            preferred = TeachingStrategy.GUIDED_PRACTICE

        # Choose preferred if available, otherwise first available
        strategy = preferred if preferred in available_strategies else available_strategies[0]

        return StrategyDecision(
            strategy=strategy,
            confidence=0.6,
            reasoning=f"Selected {strategy.value} based on phase {session.current_phase.value} and performance"
        )

    def _is_strategy_appropriate(self,
                               strategy: TeachingStrategy,
                               session: LearningSession,
                               performance: StudentPerformance) -> bool:
        """Check if a strategy is appropriate for current context"""

        if strategy == TeachingStrategy.SOCRATIC_INQUIRY:
            return performance.engagement_score > 0.4 and performance.confusion_level < 0.5
        elif strategy == TeachingStrategy.DIRECT_INSTRUCTION:
            return performance.understanding_score < 0.6 or performance.confusion_level > 0.3
        elif strategy == TeachingStrategy.GUIDED_PRACTICE:
            return performance.understanding_score > 0.4 and session.current_phase in [LearningPhase.PRACTICE, LearningPhase.EXPLORATION]
        elif strategy == TeachingStrategy.ASSESSMENT:
            return session.current_phase == LearningPhase.ASSESSMENT

        return True

    async def _generate_teaching_response(self,
                                        strategy_decision: StrategyDecision,
                                        session: LearningSession,
                                        student_model: StudentModel,
                                        topic_metadata: Optional[TopicMetadata],
                                        student_message: str) -> TeachingResponse:
        """Generate AI response using LLM with strategy-specific prompts"""

        current_performance = student_model.get_current_performance()

        # Build context for LLM
        context = {
            "student_message": student_message,
            "topic_name": topic_metadata.topic_name if topic_metadata else session.topic_id,
            "current_phase": session.current_phase.value,
            "strategy": strategy_decision.strategy.value,
            "understanding_level": current_performance.understanding_score,
            "engagement_level": current_performance.engagement_score,
            "confusion_level": current_performance.confusion_level,
            "interaction_count": session.interaction_count,
            "time_in_phase": session.time_in_current_phase().total_seconds() / 60  # minutes
        }

        # Strategy-specific prompts
        prompts = {
            TeachingStrategy.DIRECT_INSTRUCTION: self._get_direct_instruction_prompt(context),
            TeachingStrategy.SOCRATIC_INQUIRY: self._get_socratic_inquiry_prompt(context),
            TeachingStrategy.GUIDED_PRACTICE: self._get_guided_practice_prompt(context),
            TeachingStrategy.ASSESSMENT: self._get_assessment_prompt(context),
            TeachingStrategy.ENCOURAGEMENT: self._get_encouragement_prompt(context)
        }

        prompt = prompts[strategy_decision.strategy]

        # Generate response using LLM
        messages = [LLMMessage(role=MessageRole.USER, content=prompt)]
        response = await self.llm_provider.generate_response(messages)

        return TeachingResponse(
            content=response.content,
            strategy_used=strategy_decision.strategy,
            phase_used=session.current_phase,
            next_recommendations=[]
        )

    def _get_direct_instruction_prompt(self, context: Dict) -> str:
        return f"""You are an AI tutor using direct instruction to teach about {context['topic_name']}.

Student's message: "{context['student_message']}"

Current context:
- Learning phase: {context['current_phase']}
- Student understanding level: {context['understanding_level']:.1f}/1.0
- Student confusion level: {context['confusion_level']:.1f}/1.0

Provide a clear, direct explanation that:
1. Addresses the student's message
2. Explains concepts clearly and simply
3. Uses analogies or examples to make things concrete
4. Builds on what they already understand

Keep response under 200 words and ensure it's encouraging and clear."""

    def _get_socratic_inquiry_prompt(self, context: Dict) -> str:
        return f"""You are an AI tutor using Socratic questioning to guide learning about {context['topic_name']}.

Student's message: "{context['student_message']}"

Current context:
- Learning phase: {context['current_phase']}
- Student understanding level: {context['understanding_level']:.1f}/1.0
- Student engagement level: {context['engagement_level']:.1f}/1.0

Guide the student's thinking by:
1. Acknowledging their response
2. Asking thoughtful questions that lead them to deeper understanding
3. Building on their existing knowledge
4. Encouraging them to make connections

Ask 1-2 well-crafted questions. Keep response under 150 words."""

    def _get_guided_practice_prompt(self, context: Dict) -> str:
        return f"""You are an AI tutor providing guided practice for {context['topic_name']}.

Student's message: "{context['student_message']}"

Current context:
- Learning phase: {context['current_phase']}
- Student understanding level: {context['understanding_level']:.1f}/1.0

Provide guided practice by:
1. Responding to their message
2. Giving them a concrete example or exercise to work through
3. Providing step-by-step guidance
4. Encouraging them to try it themselves

Make it hands-on and practical. Keep response under 200 words."""

    def _get_assessment_prompt(self, context: Dict) -> str:
        return f"""You are an AI tutor assessing student understanding of {context['topic_name']}.

Student's message: "{context['student_message']}"

Assess their understanding by:
1. Asking a question that tests their grasp of key concepts
2. Making the question appropriately challenging but fair
3. Encouraging them to explain their reasoning

Ask one clear assessment question. Keep response under 100 words."""

    def _get_encouragement_prompt(self, context: Dict) -> str:
        return f"""You are an AI tutor providing encouragement and support for learning {context['topic_name']}.

Student's message: "{context['student_message']}"

Current context:
- Student understanding level: {context['understanding_level']:.1f}/1.0
- Student confusion level: {context['confusion_level']:.1f}/1.0

Provide encouragement by:
1. Acknowledging their effort and progress
2. Reassuring them that confusion is normal in learning
3. Giving them confidence to continue
4. Gently guiding them back on track

Be warm, supportive, and motivating. Keep response under 150 words."""

    def _update_session_state(self,
                            session: LearningSession,
                            strategy_decision: StrategyDecision,
                            analysis: InteractionAnalysis):
        """Update session state based on interaction"""

        session.interaction_count += 1

        # Simple phase transition rules
        time_in_phase = session.time_in_current_phase()

        # Transition rules based on time, performance, and phase
        if session.current_phase == LearningPhase.INTRODUCTION:
            if time_in_phase > timedelta(minutes=5) and analysis.understanding_indicators > 0.6:
                self._transition_phase(session, LearningPhase.EXPLORATION)

        elif session.current_phase == LearningPhase.EXPLORATION:
            if time_in_phase > timedelta(minutes=8) and analysis.understanding_indicators > 0.7:
                self._transition_phase(session, LearningPhase.PRACTICE)

        elif session.current_phase == LearningPhase.PRACTICE:
            if time_in_phase > timedelta(minutes=10) and analysis.understanding_indicators > 0.8:
                self._transition_phase(session, LearningPhase.ASSESSMENT)

        elif session.current_phase == LearningPhase.ASSESSMENT:
            if analysis.understanding_indicators > 0.7:
                self._transition_phase(session, LearningPhase.CONSOLIDATION)

    def _transition_phase(self, session: LearningSession, new_phase: LearningPhase):
        """Transition to a new learning phase"""
        logger.info(f"Session {session.session_id} transitioning from {session.current_phase.value} to {new_phase.value}")
        session.current_phase = new_phase
        session.phase_start_time = datetime.utcnow()

    # Helper methods for session management
    def create_session(self, student_id: str, topic_id: str, topic_metadata: Optional[TopicMetadata] = None) -> str:
        """Create a new learning session"""
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{student_id}"

        session = LearningSession(
            session_id=session_id,
            student_id=student_id,
            topic_id=topic_id
        )

        self.sessions[session_id] = session

        if topic_metadata:
            self.topic_metadata[topic_id] = topic_metadata

        # Initialize student model if doesn't exist
        if student_id not in self.student_models:
            self.student_models[student_id] = StudentModel(student_id=student_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[LearningSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_student_model(self, student_id: str) -> Optional[StudentModel]:
        """Get student model by ID"""
        return self.student_models.get(student_id)