"""SQLAlchemy models for disease catalogue and medicine recommendations."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Disease(Base):
    """
    Master catalogue of paddy diseases.
    class_index maps directly to the model's output neuron index.
    """
    __tablename__ = "diseases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ta: Mapped[str | None] = mapped_column(String(100), nullable=True)   # Tamil
    name_si: Mapped[str | None] = mapped_column(String(100), nullable=True)   # Sinhala
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="moderate")     # low|moderate|high
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="disease", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="disease"
    )

    def __repr__(self) -> str:
        return f"<Disease idx={self.class_index} name={self.name}>"


class Recommendation(Base):
    """Medicine / treatment recommendations linked to a disease."""
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    disease_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medicine_name: Mapped[str] = mapped_column(String(150), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(200), nullable=True)
    how_to_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    precautions: Mapped[str | None] = mapped_column(Text, nullable=True)
    medicine_type: Mapped[str] = mapped_column(String(50), default="fungicide")
    price_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    disease: Mapped["Disease"] = relationship("Disease", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} medicine={self.medicine_name}>"


class PreventionTip(Base):
    """Prevention tips associated with a disease."""
    __tablename__ = "prevention_tips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    disease_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tip: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)