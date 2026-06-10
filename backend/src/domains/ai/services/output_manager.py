"""Output Manager — handles AI output versioning and superseding."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from ..value_objects import ReviewState, OutputSupersessionReason


class OutputManager:
    """Manages AI output lifecycle: creation, versioning, superseding."""

    async def create_output(
        self,
        *,
        run_id: UUID,
        tenant_id: UUID,
        agent_kind: str,
        payload: dict,
        model_used: str,
        provider: str,
        cost_cents: float,
        token_usage: dict,
        review_state: ReviewState,
        domain_type: Optional[str] = None,
        domain_id: Optional[UUID] = None,
        output_repo=None,
    ) -> dict:
        """Create a new AI output record."""
        output_data = {
            "run_id": run_id,
            "tenant_id": tenant_id,
            "agent_kind": agent_kind,
            "payload": payload,
            "model_used": model_used,
            "provider": provider,
            "cost_cents": cost_cents,
            "token_usage": token_usage,
            "review_state": review_state.value,
            "domain_type": domain_type,
            "domain_id": domain_id,
            "output_version": 1,
        }
        if output_repo:
            return await output_repo.create(output_data)
        return output_data

    async def supersede_output(
        self,
        *,
        existing_output_id: UUID,
        new_payload: dict,
        reason: OutputSupersessionReason,
        reviewer_id: UUID,
        output_repo=None,
    ) -> dict:
        """Create a new output version that supersedes an existing one."""
        new_version_data = {
            "supersedes_id": existing_output_id,
            "supersession_reason": reason.value,
            "payload": new_payload,
            "review_state": ReviewState.PENDING.value,
            "reviewed_by": reviewer_id,
        }
        if output_repo:
            return await output_repo.supersede(existing_output_id, new_version_data)
        return new_version_data

    async def approve_output(
        self,
        *,
        output_id: UUID,
        reviewer_id: UUID,
        notes: Optional[str] = None,
        output_repo=None,
    ) -> dict:
        """Approve an AI output."""
        update = {
            "review_state": ReviewState.APPROVED.value,
            "reviewed_by": reviewer_id,
            "review_notes": notes,
        }
        if output_repo:
            return await output_repo.update_review(output_id, update)
        return update

    async def reject_output(
        self,
        *,
        output_id: UUID,
        reviewer_id: UUID,
        notes: Optional[str] = None,
        output_repo=None,
    ) -> dict:
        """Reject an AI output."""
        update = {
            "review_state": ReviewState.REJECTED.value,
            "reviewed_by": reviewer_id,
            "review_notes": notes,
        }
        if output_repo:
            return await output_repo.update_review(output_id, update)
        return update