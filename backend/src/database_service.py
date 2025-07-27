"""
Database service for PostgreSQL using SQLAlchemy.

Simplified service focused on bite-sized topics storage.
"""

from sqlalchemy import create_engine, desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.config.config import config_manager
from src.data_structures import (
    Base,
    BiteSizedComponent,
    BiteSizedTopic,
    ComponentData,
    TopicResult,
    PodcastEpisode,
    PodcastSegment,
    TopicPodcastLink,
    PodcastEpisodeData,
    PodcastSegmentData,
)


class DatabaseService:
    """
    PostgreSQL-based database service using SQLAlchemy.

    Simplified service focused on bite-sized topics functionality.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """
        Initialize the database service.

        Args:
            database_url: Optional database URL override
        """
        if database_url:
            self.database_url = database_url
        else:
            self.database_url = config_manager.get_database_url()

        # Create SQLAlchemy engine
        self.engine = create_engine(
            self.database_url,
            echo=config_manager.config.database_echo,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
        )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Initialize database schema
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema"""
        try:
            Base.metadata.create_all(bind=self.engine)
        except SQLAlchemyError as e:
            print(f"Error initializing database: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def close_session(self, session: Session) -> None:
        """Close a database session"""
        session.close()

    # Bite-sized topic methods
    def get_bite_sized_topic(self, topic_id: str) -> TopicResult | None:
        """Get a bite-sized topic by ID, returned as Pydantic model"""
        session = self.get_session()
        try:
            topic = session.get(BiteSizedTopic, topic_id)
            if not topic:
                return None

            # Convert SQLAlchemy model to Pydantic model
            return TopicResult(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives or [],
                key_concepts=topic.key_concepts or [],
                key_aspects=topic.key_aspects or [],
                target_insights=topic.target_insights or [],
                source_material=topic.source_material,
                source_domain=topic.source_domain,
                source_level=topic.source_level,
                refined_material=topic.refined_material,
                created_at=topic.created_at,
                updated_at=topic.updated_at,
            )
        except SQLAlchemyError as e:
            print(f"Error getting bite-sized topic: {e}")
            return None
        finally:
            self.close_session(session)

    def list_bite_sized_topics(self, limit: int = 100) -> list[TopicResult]:
        """List bite-sized topics, returned as Pydantic models"""
        session = self.get_session()
        try:
            stmt = select(BiteSizedTopic).limit(limit).order_by(desc(BiteSizedTopic.created_at))
            result = session.execute(stmt)
            topics = result.scalars().all()

            # Convert SQLAlchemy models to Pydantic models
            return [
                TopicResult(
                    id=topic.id,
                    title=topic.title,
                    core_concept=topic.core_concept,
                    user_level=topic.user_level,
                    learning_objectives=topic.learning_objectives or [],
                    key_concepts=topic.key_concepts or [],
                    key_aspects=topic.key_aspects or [],
                    target_insights=topic.target_insights or [],
                    source_material=topic.source_material,
                    source_domain=topic.source_domain,
                    source_level=topic.source_level,
                    refined_material=topic.refined_material,
                    created_at=topic.created_at,
                    updated_at=topic.updated_at,
                )
                for topic in topics
            ]
        except SQLAlchemyError as e:
            print(f"Error listing bite-sized topics: {e}")
            return []
        finally:
            self.close_session(session)

    def save_bite_sized_topic(self, topic: BiteSizedTopic) -> bool:
        """Save a bite-sized topic"""
        session = self.get_session()
        try:
            session.add(topic)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving bite-sized topic: {e}")
            return False
        finally:
            self.close_session(session)

    def delete_bite_sized_topic(self, topic_id: str) -> bool:
        """Delete a bite-sized topic"""
        session = self.get_session()
        try:
            topic = session.get(BiteSizedTopic, topic_id)
            if topic:
                session.delete(topic)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error deleting bite-sized topic: {e}")
            return False
        finally:
            self.close_session(session)

    def get_topic_components(self, topic_id: str) -> list[ComponentData]:
        """Get all components for a topic, returned as Pydantic models"""
        session = self.get_session()
        try:
            stmt = select(BiteSizedComponent).where(BiteSizedComponent.topic_id == topic_id)
            result = session.execute(stmt)
            components = result.scalars().all()

            # Convert SQLAlchemy models to Pydantic models
            return [
                ComponentData(
                    id=comp.id,
                    topic_id=comp.topic_id,
                    component_type=comp.component_type,
                    title=comp.title,
                    content=comp.content,
                    generation_prompt=comp.generation_prompt,
                    raw_llm_response=comp.raw_llm_response,
                    evaluation=comp.evaluation,
                    created_at=comp.created_at,
                    updated_at=comp.updated_at,
                )
                for comp in components
            ]
        except SQLAlchemyError as e:
            print(f"Error getting topic components: {e}")
            return []
        finally:
            self.close_session(session)

    # Podcast methods
    def get_podcast_episode(self, episode_id: str) -> PodcastEpisodeData | None:
        """Get a podcast episode by ID, returned as Pydantic model"""
        session = self.get_session()
        try:
            episode = session.get(PodcastEpisode, episode_id)
            if not episode:
                return None

            # Get segments for this episode
            segments = session.query(PodcastSegment).where(
                PodcastSegment.episode_id == episode_id
            ).order_by(PodcastSegment.order_index).all()

            # Get primary topic link
            primary_link = session.query(TopicPodcastLink).where(
                TopicPodcastLink.podcast_id == episode_id,
                TopicPodcastLink.is_primary_topic == 1
            ).first()

            # Convert SQLAlchemy models to Pydantic models
            segment_data = [
                PodcastSegmentData(
                    id=seg.id,
                    episode_id=seg.episode_id,
                    segment_type=seg.segment_type,
                    title=seg.title,
                    script_content=seg.script_content,
                    estimated_duration_seconds=seg.estimated_duration_seconds,
                    order_index=seg.order_index,
                    created_at=seg.created_at,
                    updated_at=seg.updated_at,
                )
                for seg in segments
            ]

            return PodcastEpisodeData(
                id=episode.id,
                title=episode.title,
                description=episode.description,
                learning_outcomes=episode.learning_outcomes or [],
                total_duration_minutes=episode.total_duration_minutes,
                full_script=episode.full_script,
                segments=segment_data,
                primary_topic_id=primary_link.topic_id if primary_link else "",
                created_at=episode.created_at,
                updated_at=episode.updated_at,
            )
        except SQLAlchemyError as e:
            print(f"Error getting podcast episode: {e}")
            return None
        finally:
            self.close_session(session)

    def get_topic_podcast(self, topic_id: str) -> PodcastEpisodeData | None:
        """Get the podcast episode linked to a topic"""
        session = self.get_session()
        try:
            # Find the primary link for this topic
            link = session.query(TopicPodcastLink).where(
                TopicPodcastLink.topic_id == topic_id,
                TopicPodcastLink.is_primary_topic == 1
            ).first()

            if not link:
                return None

            # Get the podcast episode
            return self.get_podcast_episode(link.podcast_id)
        except SQLAlchemyError as e:
            print(f"Error getting topic podcast: {e}")
            return None
        finally:
            self.close_session(session)

    def save_podcast_episode(self, episode: PodcastEpisode) -> bool:
        """Save a podcast episode"""
        session = self.get_session()
        try:
            session.add(episode)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving podcast episode: {e}")
            return False
        finally:
            self.close_session(session)

    def save_podcast_segment(self, segment: PodcastSegment) -> bool:
        """Save a podcast segment"""
        session = self.get_session()
        try:
            session.add(segment)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving podcast segment: {e}")
            return False
        finally:
            self.close_session(session)

    def save_topic_podcast_link(self, link: TopicPodcastLink) -> bool:
        """Save a topic-podcast link"""
        session = self.get_session()
        try:
            session.add(link)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving topic-podcast link: {e}")
            return False
        finally:
            self.close_session(session)


# Global database service instance
_database_service: DatabaseService | None = None


def init_database_service(database_url: str | None = None) -> DatabaseService:
    """Initialize the global database service"""
    global _database_service  # noqa: PLW0603
    _database_service = DatabaseService(database_url)
    print(f"Initialized database service: {_database_service}")
    return _database_service


def get_database_service() -> DatabaseService | None:
    """Get the global database service instance, initializing if needed"""
    global _database_service  # noqa: PLW0603

    print(f"Getting database service: {_database_service}")

    # Lazy initialization - initialize if not already done
    if _database_service is None:
        try:
            print("Database service not initialized, initializing now...")
            _database_service = DatabaseService()
            print(f"Lazy initialization successful: {_database_service}")
        except Exception as e:
            print(f"Failed to lazy initialize database service: {e}")
            return None

    return _database_service
