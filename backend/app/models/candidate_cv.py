from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CandidateCV(Base):
    __tablename__ = "candidate_cvs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_offer_id = Column(
        Integer,
        ForeignKey("job_offers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True, index=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    extracted_text = Column(Text, nullable=True)
    processing_status = Column(
        String(50),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
        index=True
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    error_message = Column(Text, nullable=True)
    application_status = Column(
        String(30),
        nullable=False,
        default="PENDIENTE",
        server_default="PENDIENTE",
        index=True,
    )
    extraction_status = Column(
        String(30),
        nullable=False,
        default="PENDIENTE",
        server_default="PENDIENTE",
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to JobOffer
    job_offer = relationship("JobOffer", back_populates="cvs")

    # Relationship to CandidateEvaluation (1:1)
    evaluation = relationship(
        "CandidateEvaluation",
        back_populates="cv",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<CandidateCV(id={self.id}, offer_id={self.job_offer_id}, file='{self.original_filename}', status='{self.processing_status}')>"
