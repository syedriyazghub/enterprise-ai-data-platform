"""
Auto Schema Mapping Service

Uses LLM to automatically map source fields to target schema,
e.g., "Customer Name" → "customer_name", "Cust. ID" → "customer_id"
"""
from typing import Any
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class AutoMappingService:
    """LLM-powered automatic field mapping between schemas."""

    async def map_fields(
        self,
        source_fields: list[str],
        target_schema: dict[str, str],  # field_name -> description
    ) -> dict[str, str]:
        """Map source fields to target schema fields."""
        if not settings.OPENAI_API_KEY:
            return self._rule_based_mapping(source_fields, list(target_schema.keys()))

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        target_desc = "\n".join(f"- {k}: {v}" for k, v in target_schema.items())
        source_list = "\n".join(f"- {f}" for f in source_fields)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a data mapping expert. Map source fields to target fields. Return JSON object where keys are source fields and values are target fields. Use null if no match.",
                },
                {
                    "role": "user",
                    "content": f"Source fields:\n{source_list}\n\nTarget schema:\n{target_desc}",
                },
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content)

    def _rule_based_mapping(self, source_fields: list[str], target_fields: list[str]) -> dict[str, str]:
        """Fallback rule-based mapping using string similarity."""
        from difflib import get_close_matches
        mapping = {}
        for src in source_fields:
            normalized = src.lower().replace(" ", "_").replace("-", "_")
            matches = get_close_matches(normalized, [t.lower() for t in target_fields], n=1, cutoff=0.6)
            if matches:
                target_idx = [t.lower() for t in target_fields].index(matches[0])
                mapping[src] = target_fields[target_idx]
            else:
                mapping[src] = None
        return mapping

    async def suggest_transformations(
        self,
        source_sample: dict[str, Any],
        target_schema: dict[str, str],
    ) -> list[dict]:
        """Suggest data transformations needed for mapping."""
        if not settings.OPENAI_API_KEY:
            return []

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Suggest data transformations needed to convert source data to target schema. Return JSON array of {field, transformation, reason}.",
                },
                {
                    "role": "user",
                    "content": f"Source sample: {source_sample}\nTarget schema: {target_schema}",
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get("transformations", [])
