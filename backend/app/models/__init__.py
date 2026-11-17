"""SQLAlchemy models — import all models here so Alembic picks them up."""

from app.models.assistant import AIConversation, AIMessage
from app.models.base import Base
from app.models.card import CreditCard
from app.models.document import Document, DocumentChunk
from app.models.email import EmailConnection, EmailImport
from app.models.payment import Payment
from app.models.reward import RewardCap, RewardLedger, RewardProgram, RewardRule
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.user import User

__all__ = [
    "AIConversation",
    "AIMessage",
    "Base",
    "CreditCard",
    "Document",
    "DocumentChunk",
    "EmailConnection",
    "EmailImport",
    "Payment",
    "RewardProgram",
    "RewardRule",
    "RewardCap",
    "RewardLedger",
    "Statement",
    "Transaction",
    "User",
]
