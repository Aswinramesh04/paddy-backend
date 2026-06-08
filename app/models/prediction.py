"""SQLAlchemy model for disease prediction records (scan history)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    disease_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("diseases.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Image info
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    image_filename: Mapped[str] = mapped_column(String(256), nullable=False)

    # Prediction results
    predicted_class: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="moderate")

    # All class probabilities stored as JSON string
    all_probabilities: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Processing metadata
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    status: Mapped[str] = mapped_column(String(20), default="completed")  # processing|completed|failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="predictions")  # noqa: F821
    disease: Mapped["Disease | None"] = relationship("Disease", back_populates="predictions")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} class={self.predicted_class} conf={self.confidence:.2f}>"