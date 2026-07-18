"""Business rules CRUD and evaluation endpoints."""
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.rules.business_rules import BusinessRulesEngine, BusinessRule

router = APIRouter()


class BusinessRuleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    field: str = Field(..., min_length=1)
    expression: str = Field(..., min_length=1, description="Python expression, e.g. 'value > 0'")
    severity: str = "error"
    domain: str = ""
    tags: list[str] = Field(default_factory=list)
    tenant_id: str = "default"


class EvaluateRulesRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)
    tenant_id: str = "default"
    domain: str = ""


@router.post("/", status_code=201)
async def create_rule(payload: BusinessRuleCreate):
    """Create a custom business rule."""
    engine = BusinessRulesEngine()
    rule = BusinessRule(
        tenant_id=payload.tenant_id,
        name=payload.name,
        description=payload.description,
        field=payload.field,
        expression=payload.expression,
        severity=payload.severity,
        domain=payload.domain,
        tags=payload.tags,
    )
    saved = engine.save_rule(rule)
    return {"rule_id": saved.rule_id, "name": saved.name, "field": saved.field}


@router.get("/")
async def list_rules(
    tenant_id: str = Query("default"),
    domain: str = Query(""),
):
    """List all active business rules for a tenant."""
    engine = BusinessRulesEngine()
    rules = engine.list_rules(tenant_id=tenant_id, domain=domain)
    return {"rules": [r.__dict__ for r in rules], "total": len(rules)}


@router.get("/{rule_id}")
async def get_rule(rule_id: str, tenant_id: str = Query("default")):
    """Get a specific business rule."""
    engine = BusinessRulesEngine()
    rule = engine.get_rule(tenant_id=tenant_id, rule_id=rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.__dict__


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, tenant_id: str = Query("default")):
    """Delete a business rule."""
    engine = BusinessRulesEngine()
    deleted = engine.delete_rule(tenant_id=tenant_id, rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")


@router.post("/evaluate")
async def evaluate_rules(request: EvaluateRulesRequest):
    """Evaluate all active business rules against a dataset."""
    engine = BusinessRulesEngine()
    rules = engine.list_rules(tenant_id=request.tenant_id, domain=request.domain)
    if not rules:
        return {"message": "No active rules found", "results": [], "total_records": len(request.records)}

    all_results = engine.evaluate(request.records, rules)
    total_failures = sum(
        1 for record_results in all_results
        for r in record_results if not r.passed
    )
    return {
        "total_records": len(request.records),
        "total_rules": len(rules),
        "total_failures": total_failures,
        "results": [
            [r.__dict__ for r in record_results]
            for record_results in all_results
        ],
    }
