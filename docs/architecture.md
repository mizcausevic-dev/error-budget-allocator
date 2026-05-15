# Architecture

`error-budget-allocator` is a Python and FastAPI service for turning **error-budget consumption into an operator decision surface**.

It focuses on the reliability questions that usually get buried underneath dashboards:

- which services are already burning too fast
- which services are projected to breach before the month closes
- which healthy lanes can lend budget headroom
- which teams should freeze or slow changes before shared reliability margin disappears

## Core model

The service works from a seeded fleet model in [app/data/sample_budget_data.json](/C:/Users/chaus/dev/repos/error-budget-allocator/app/data/sample_budget_data.json).

Each service carries:

- service identity and owner
- tier and environment
- SLO target
- monthly budget minutes
- consumed and projected consumed minutes
- dependency pressure
- deploy-window risk
- change failure rate
- critical incident count
- recovery-drill recency

## Evaluation flow

The allocator service in [app/services/allocator_service.py](/C:/Users/chaus/dev/repos/error-budget-allocator/app/services/allocator_service.py) computes:

1. live burn percentage
2. projected burn percentage
3. remaining budget minutes
4. projected overrun minutes
5. risk score
6. verdict: `healthy`, `watch`, or `breach`
7. suggested budget shift and source candidates

The score deliberately mixes burn posture with operational context so a service cannot hide behind one good metric while another signal is screaming.

## UI surfaces

The HTML proof layer in [app/render.py](/C:/Users/chaus/dev/repos/error-budget-allocator/app/render.py) exposes:

- `/`
  Reliability overview with headroom, projected overrun, and top burn lanes.
- `/allocations`
  Prioritized queue showing which services need relief first.
- `/service-matrix`
  Compact matrix for burn, overrun, dependency pressure, and verdict.
- `/methodology`
  Explains how the allocator scores pressure and why.
- `/api-summary`
  Shows how the JSON surface can plug into broader workflow automation.

## API layer

The FastAPI app in [app/main.py](/C:/Users/chaus/dev/repos/error-budget-allocator/app/main.py) exposes both human-readable views and machine-consumable endpoints so the same allocation logic can feed dashboards, release gates, or incident-review tooling.

## Validation

The repo includes:

- unit tests in [tests/test_allocator_service.py](/C:/Users/chaus/dev/repos/error-budget-allocator/tests/test_allocator_service.py)
- smoke checks in [scripts/smoke_check.py](/C:/Users/chaus/dev/repos/error-budget-allocator/scripts/smoke_check.py)
- proof asset generation in [scripts/render_readme_assets.py](/C:/Users/chaus/dev/repos/error-budget-allocator/scripts/render_readme_assets.py)
- GitHub Actions CI in [.github/workflows/ci.yml](/C:/Users/chaus/dev/repos/error-budget-allocator/.github/workflows/ci.yml)
