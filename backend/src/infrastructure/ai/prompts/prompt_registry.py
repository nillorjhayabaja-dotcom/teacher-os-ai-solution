"""Prompt Registry — manages versioned prompt templates."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class PromptRegistry:
    """Central registry for versioned prompt templates.

    Manages prompt creation, versioning, activation, and retrieval.
    """

    def __init__(self, session=None) -> None:
        self._session = session
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get_prompt(self, prompt_id: UUID) -> Optional[Dict[str, Any]]:
        return self._cache.get(str(prompt_id))

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """Return all prompts in the registry."""
        return list(self._cache.values())

    async def get_active_version(self, agent_kind: str, category: str = "system") -> Optional[Dict[str, Any]]:
        for entry in self._cache.values():
            if entry.get("agent_kind") == agent_kind and entry.get("category") == category and entry.get("is_active"):
                return entry
        return None

    async def create_prompt(
        self,
        *,
        name: str,
        description: str,
        category: str,
        agent_kind: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        prompt_id = str(uuid4())
        entry = {
            "id": prompt_id,
            "name": name,
            "description": description,
            "category": category,
            "agent_kind": agent_kind,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "is_active": True,
            "versions": [],
        }
        self._cache[prompt_id] = entry
        return entry

    async def create_version(
        self,
        *,
        prompt_id: UUID,
        system_prompt: str,
        user_template: str,
        few_shot_examples: List[Dict] = None,
        variables: List[str] = None,
        output_schema: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        entry = self._cache.get(str(prompt_id))
        if not entry:
            entry = {
                "id": str(prompt_id),
                "name": f"auto-{prompt_id}",
                "description": "Auto-created on version creation",
                "category": "system",
                "agent_kind": None,
                "tenant_id": None,
                "is_active": True,
                "versions": [],
            }
            self._cache[str(prompt_id)] = entry

        version_num = len(entry["versions"]) + 1
        version = {
            "id": str(uuid4()),
            "prompt_id": str(prompt_id),
            "version_number": version_num,
            "system_prompt": system_prompt,
            "user_template": user_template,
            "few_shot_examples": few_shot_examples or [],
            "variables": variables or [],
            "output_schema": output_schema,
            "is_active": True,
        }
        entry["versions"].append(version)
        return version

    async def activate_version(self, prompt_id: UUID, version_id: UUID) -> None:
        entry = self._cache.get(str(prompt_id))
        if not entry:
            raise KeyError(f"Prompt not found: {prompt_id}")
        for version in entry["versions"]:
            version["is_active"] = version["id"] == str(version_id)