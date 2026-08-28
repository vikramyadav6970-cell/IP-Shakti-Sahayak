from sqlalchemy import String, ForeignKey, Enum, Boolean, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum
import uuid

class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"

class ExpertRequestStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"

class Conversation(BaseModel):
    __tablename__ = "conversations"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(BaseModel):
    __tablename__ = "messages"
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    citations: Mapped[list["Citation"]] = relationship("Citation", back_populates="message", cascade="all, delete-orphan")

class Citation(BaseModel):
    __tablename__ = "citations"
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), index=True)
    message: Mapped["Message"] = relationship("Message", back_populates="citations")
    document_title: Mapped[str] = mapped_column(String(255))
    section_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    corpus_collection: Mapped[str] = mapped_column(String(100), index=True)

class Feedback(BaseModel):
    __tablename__ = "feedback"
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

class ExpertRequest(BaseModel):
    __tablename__ = "expert_requests"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True, index=True)
    status: Mapped[ExpertRequestStatus] = mapped_column(Enum(ExpertRequestStatus), default=ExpertRequestStatus.OPEN, index=True)
    context: Mapped[str] = mapped_column(Text)
