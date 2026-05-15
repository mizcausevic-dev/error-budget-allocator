from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.render import (
    render_allocation_queue,
    render_api_summary,
    render_burn_methodology,
    render_overview,
    render_service_matrix,
)
from app.services.allocator_service import build_service

app = FastAPI(
    title="Error Budget Allocator",
    version="0.1.0",
    description=(
        "FastAPI reliability control surface for allocating error-budget burn across services, "
        "dependencies, deploy windows, and operational ownership lanes."
    ),
)

SERVICE = build_service()


@app.get("/", response_class=HTMLResponse)
def overview() -> str:
    return render_overview()


@app.get("/allocations", response_class=HTMLResponse)
def allocations() -> str:
    return render_allocation_queue()


@app.get("/service-matrix", response_class=HTMLResponse)
def service_matrix() -> str:
    return render_service_matrix()


@app.get("/methodology", response_class=HTMLResponse)
def methodology() -> str:
    return render_burn_methodology()


@app.get("/api-summary", response_class=HTMLResponse)
def api_summary() -> str:
    return render_api_summary()


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict:
    return SERVICE.summary()


@app.get("/api/services")
def services() -> list[dict]:
    return SERVICE.service_catalog()


@app.get("/api/services/{service_id}")
def service_detail(service_id: str) -> dict:
    service = SERVICE.service_detail(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@app.get("/api/allocations")
def allocations_api() -> list[dict]:
    return SERVICE.allocation_queue()


@app.get("/api/owners")
def owner_allocations() -> list[dict]:
    return SERVICE.owner_allocations()


@app.get("/api/burn-matrix")
def burn_matrix() -> list[dict]:
    return SERVICE.burn_matrix()


@app.get("/api/sample")
def sample() -> dict:
    return SERVICE.sample_payload()


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", "4948"))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
