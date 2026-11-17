"""Document knowledge ingestion, text chunking, and policy seeding service (Phase 9)."""

from __future__ import annotations

import hashlib
import io
import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import CreditCard
from app.models.document import Document, DocumentChunk
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider


def chunk_text(text: str, page_number: int, chunk_size_words: int = 250, overlap_words: int = 40) -> list[dict[str, Any]]:
    """Splits text into overlapping word chunks preserving page attribution."""
    words = text.split()
    if not words:
        return []

    chunks = []
    idx = 0
    step = max(1, chunk_size_words - overlap_words)

    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size_words]
        chunk_str = " ".join(chunk_words)
        chunks.append(
            {
                "chunk_index": idx,
                "page_number": page_number,
                "content": chunk_str,
                "token_count": len(chunk_words),
            }
        )
        idx += 1
        if i + chunk_size_words >= len(words):
            break

    return chunks


class DocumentService:
    """Manages policy document uploads, semantic chunk extraction, and bank fixtures."""

    @classmethod
    async def ingest_document(
        cls,
        db: AsyncSession,
        storage: StorageProvider,
        user_id: uuid.UUID,
        file_bytes: bytes,
        file_name: str,
        title: str,
        doc_type: str = "policy",
        card_id: uuid.UUID | None = None,
    ) -> Document:
        """Ingest policy PDF, extract pages, chunk content, and index."""
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Check duplicate
        existing = (
            await db.execute(
                select(Document).where(
                    Document.user_id == user_id,
                    Document.file_sha256 == file_sha256,
                )
            )
        ).scalar_one_or_none()
        if existing:
            return existing

        # Extract text via pypdf
        reader = PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)

        # Save to storage
        dest_rel = f"policies/{user_id}/{file_sha256[:16]}_{file_name}"
        saved_path = await storage.save(file_bytes, dest_rel)

        doc = Document(
            user_id=user_id,
            card_id=card_id,
            title=title,
            doc_type=doc_type,
            file_path=saved_path,
            file_name=file_name,
            file_size_bytes=len(file_bytes),
            file_sha256=file_sha256,
            total_pages=total_pages,
            status="processed",
        )
        db.add(doc)
        await db.flush()

        # Chunk all pages
        chunk_index = 0
        for p_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_chunks = chunk_text(page_text, page_number=p_idx + 1)

            for pc in page_chunks:
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_index,
                    page_number=pc["page_number"],
                    content=pc["content"],
                    token_count=pc["token_count"],
                    metadata_json={"page": pc["page_number"]},
                )
                db.add(chunk_record)
                chunk_index += 1

        await db.commit()
        await db.refresh(doc)
        return doc

    @classmethod
    async def seed_default_policies(cls, db: AsyncSession, user_id: uuid.UUID) -> int:
        """Seeds realistic official card terms & conditions knowledge fixtures."""
        card_stmt = select(CreditCard).where(CreditCard.user_id == user_id, CreditCard.status == "active")
        cards = list((await db.execute(card_stmt)).scalars().all())

        card_by_issuer: dict[str, CreditCard] = {c.issuer.lower(): c for c in cards}

        fixtures = [
            {
                "title": "Amazon Pay ICICI Cardmember Agreement & Cashback Terms",
                "issuer_key": "icici",
                "doc_type": "terms_and_conditions",
                "file_name": "ICICI_Amazon_Pay_Terms_2026.pdf",
                "pages": [
                    (
                        "1. REWARD ACCRUAL CONDITIONS: Cardmembers who are active Amazon Prime members earn 5% unlimited cashback "
                        "on all retail eligible purchases made on Amazon.in. Non-Prime members earn 3% cashback on Amazon.in. "
                        "2% cashback is awarded on digital recharges, bill payments, and flight bookings made via Amazon Pay. "
                        "1% cashback is awarded on all other retail transactions without any upper capping or expiration date."
                    ),
                    (
                        "2. MANDATORY REWARD EXCLUSIONS: The following transaction categories are completely excluded from earning any cashback: "
                        "(a) Fuel and petroleum product purchases at any petrol pump station. "
                        "(b) Purchase of Gold, Silver, Jewellery, or precious stones. "
                        "(c) Wallet reload transactions (including Paytm, Mobikwik, PhonePe wallet loads). "
                        "(d) Rent payments made through aggregators or third-party platforms. "
                        "(e) Government tax payments, property taxes, and utility surcharge fees. "
                        "(f) Cash withdrawals at ATMs or cash advance fees."
                    ),
                ],
            },
            {
                "title": "HDFC Bank Millennia Credit Card Reward Points Circular",
                "issuer_key": "hdfc",
                "doc_type": "policy",
                "file_name": "HDFC_Millennia_Rewards_Circular.pdf",
                "pages": [
                    (
                        "1. CASHPOINTS PROGRAM SPECIFICATIONS: Cardmembers receive 5% CashPoints on transactions executed with partner merchants: "
                        "Amazon India, Flipkart, Swiggy, Zomato, Uber, Myntra, Tata CLiQ, Cult.fit, Sony LIV, and BookMyShow. "
                        "1% CashPoints is awarded on all other retail domestic and international spends. "
                        "Minimum transaction spend threshold of Rs 100 is required to earn CashPoints."
                    ),
                    (
                        "2. CAP LIMITS AND CONSTRAINTS: "
                        "(a) Partner Merchant Spend Cap: Maximum 1,000 CashPoints per calendar month across all 5% accelerated partner merchants combined. "
                        "(b) Other Spends Cap: Maximum 1,000 CashPoints per calendar month on all 1% eligible retail spends. "
                        "Once the cap of 1,000 CashPoints is reached within a calendar month, no further CashPoints will be accrued for that category until the 1st of the next month."
                    ),
                    (
                        "3. EXCLUSIONS & DEVALUATIONS: Fuel transactions, EMI transactions, wallet loading, rent payments, educational fee payments, "
                        "and government service payments do not qualify for CashPoints. "
                        "CashPoints expire after 2 years from the date of accumulation if not redeemed."
                    ),
                ],
            },
            {
                "title": "HSBC Cashback / Live+ Credit Card Benefit Terms",
                "issuer_key": "hsbc",
                "doc_type": "fee_schedule",
                "file_name": "HSBC_LivePlus_Cashback_Terms.pdf",
                "pages": [
                    (
                        "1. ACCELERATED CASHBACK BENEFITS: Enjoy 10% accelerated cashback on Food & Dining, Food Delivery apps (Zomato, Swiggy), "
                        "and Grocery purchases (Blinkit, Zepto, Instamart, Nature's Basket). "
                        "All other eligible domestic retail spends earn 1.5% unlimited cashback credited directly to your monthly statement."
                    ),
                    (
                        "2. CAP CONSTRAINTS AND BILLING CYCLE DATES: "
                        "The 10% accelerated dining and grocery cashback is capped at a maximum of Rs 1,000 per billing cycle. "
                        "The cap resets strictly on the statement generation date of each billing cycle, not on calendar month boundaries."
                    ),
                    (
                        "3. EXCLUDED SPEND CATEGORIES: Fuel spends, cash advance transactions, forex remittances, rent payments, and wallet loads "
                        "are strictly excluded from cashback calculations."
                    ),
                ],
            },
        ]

        seeded_count = 0
        for f in fixtures:
            # Check existing by title
            exists = (
                await db.execute(
                    select(Document).where(
                        Document.user_id == user_id,
                        Document.title == f["title"],
                    )
                )
            ).scalar_one_or_none()

            if exists:
                continue

            card = card_by_issuer.get(f["issuer_key"])
            card_id = card.id if card else None

            fake_sha = hashlib.sha256(f["title"].encode("utf-8")).hexdigest()
            doc = Document(
                user_id=user_id,
                card_id=card_id,
                title=f["title"],
                doc_type=f["doc_type"],
                file_path=f"policies/{user_id}/{fake_sha[:16]}_{f['file_name']}",
                file_name=f["file_name"],
                file_size_bytes=1024 * len(f["pages"]),
                file_sha256=fake_sha,
                total_pages=len(f["pages"]),
                status="processed",
            )
            db.add(doc)
            await db.flush()

            chunk_idx = 0
            for page_num, text in enumerate(f["pages"], start=1):
                chunks = chunk_text(text, page_number=page_num, chunk_size_words=200)
                for c in chunks:
                    chunk_rec = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=chunk_idx,
                        page_number=c["page_number"],
                        content=c["content"],
                        token_count=c["token_count"],
                        metadata_json={"page": c["page_number"]},
                    )
                    db.add(chunk_rec)
                    chunk_idx += 1

            seeded_count += 1

        await db.commit()
        return seeded_count
