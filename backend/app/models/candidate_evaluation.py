from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cv_id = Column(
        Integer,
        ForeignKey("candidate_cvs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    score = Column(Integer, nullable=False)
    recommendation = Column(String(50), nullable=False, index=True)  # recommended, review, not_recommended
    experience_range = Column(String(20), nullable=False, default="0-2")
    education_level = Column(String(20), nullable=False, default="técnico")
    matched_required_skills = Column(JSON, nullable=False, default=list)
    missing_required_skills = Column(JSON, nullable=False, default=list)
    matched_preferred_skills = Column(JSON, nullable=False, default=list)
    experience_analysis = Column(Text, nullable=False)
    requirements_analysis = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False, default="openrouter/free")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to CandidateCV (1:1)
    cv = relationship("CandidateCV", back_populates="evaluation")

    def __repr__(self) -> str:
        return f"<CandidateEvaluation(id={self.id}, cv_id={self.cv_id}, score={self.score}, recommendation='{self.recommendation}')>"
