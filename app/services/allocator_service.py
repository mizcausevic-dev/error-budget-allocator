from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_budget_data.json"


@dataclass
class ErrorBudgetAllocatorService:
    services: list[dict]

    def summary(self) -> dict:
        evaluations = self._evaluations()
        service_lookup = {service["serviceId"]: service for service in self.services}
        total_budget = round(sum(item["monthlyBudgetMinutes"] for item in self.services), 1)
        total_consumed = round(sum(item["consumedMinutes"] for item in self.services), 1)
        total_projected = round(sum(item["projectedConsumedMinutes"] for item in self.services), 1)
        projected_overrun = round(max(0.0, total_projected - total_budget), 1)
        healthy_count = sum(1 for item in evaluations if item["verdict"] == "healthy")
        watch_count = sum(1 for item in evaluations if item["verdict"] == "watch")
        breach_count = sum(1 for item in evaluations if item["verdict"] == "breach")

        hottest_service = max(evaluations, key=lambda item: item["riskScore"])
        return {
            "serviceCount": len(self.services),
            "ownerCount": len({service["owner"] for service in self.services}),
            "totalBudgetMinutes": total_budget,
            "consumedMinutes": total_consumed,
            "projectedConsumedMinutes": total_projected,
            "projectedOverrunMinutes": projected_overrun,
            "healthyCount": healthy_count,
            "watchCount": watch_count,
            "breachCount": breach_count,
            "averageBurnPct": round(mean(item["burnPct"] for item in evaluations), 1),
            "averageProjectedPct": round(mean(item["projectedBurnPct"] for item in evaluations), 1),
            "hottestService": service_lookup[hottest_service["serviceId"]]["name"],
            "leadRecommendation": self._lead_recommendation(evaluations),
        }

    def service_catalog(self) -> list[dict]:
        evaluations = {item["serviceId"]: item for item in self._evaluations()}
        rows: list[dict] = []
        for service in self.services:
            evaluation = evaluations[service["serviceId"]]
            rows.append(
                {
                    "serviceId": service["serviceId"],
                    "name": service["name"],
                    "owner": service["owner"],
                    "tier": service["tier"],
                    "environment": service["environment"],
                    "sloTarget": service["sloTarget"],
                    "monthlyBudgetMinutes": service["monthlyBudgetMinutes"],
                    "consumedMinutes": service["consumedMinutes"],
                    "projectedConsumedMinutes": service["projectedConsumedMinutes"],
                    "remainingMinutes": evaluation["remainingMinutes"],
                    "projectedOverrunMinutes": evaluation["projectedOverrunMinutes"],
                    "burnPct": evaluation["burnPct"],
                    "projectedBurnPct": evaluation["projectedBurnPct"],
                    "dependencyPressure": service["dependencyPressure"],
                    "riskScore": evaluation["riskScore"],
                    "verdict": evaluation["verdict"],
                    "topConcern": evaluation["topConcern"],
                    "nextAction": evaluation["nextAction"],
                }
            )
        return sorted(rows, key=lambda row: (row["riskScore"], row["projectedBurnPct"]), reverse=True)

    def service_detail(self, service_id: str) -> dict | None:
        service = next((item for item in self.services if item["serviceId"] == service_id), None)
        if service is None:
            return None
        evaluation = self._evaluate_service(service)
        return {
            **service,
            "evaluation": evaluation,
            "sourceCandidates": self._source_candidates(service["serviceId"]),
        }

    def allocation_queue(self) -> list[dict]:
        queue: list[dict] = []
        for service in self.services:
            evaluation = self._evaluate_service(service)
            if evaluation["verdict"] == "healthy":
                continue
            queue.append(
                {
                    "serviceId": service["serviceId"],
                    "name": service["name"],
                    "owner": service["owner"],
                    "tier": service["tier"],
                    "riskScore": evaluation["riskScore"],
                    "verdict": evaluation["verdict"],
                    "burnPct": evaluation["burnPct"],
                    "projectedBurnPct": evaluation["projectedBurnPct"],
                    "budgetShiftMinutes": evaluation["budgetShiftMinutes"],
                    "topConcern": evaluation["topConcern"],
                    "nextAction": evaluation["nextAction"],
                    "sourceCandidates": self._source_candidates(service["serviceId"]),
                }
            )
        return sorted(queue, key=lambda item: (item["riskScore"], item["projectedBurnPct"]), reverse=True)

    def burn_matrix(self) -> list[dict]:
        rows: list[dict] = []
        for service in self.services:
            evaluation = self._evaluate_service(service)
            rows.append(
                {
                    "serviceId": service["serviceId"],
                    "name": service["name"],
                    "owner": service["owner"],
                    "tier": service["tier"],
                    "consumedMinutes": service["consumedMinutes"],
                    "monthlyBudgetMinutes": service["monthlyBudgetMinutes"],
                    "projectedConsumedMinutes": service["projectedConsumedMinutes"],
                    "remainingMinutes": evaluation["remainingMinutes"],
                    "burnPct": evaluation["burnPct"],
                    "projectedBurnPct": evaluation["projectedBurnPct"],
                    "dependencyPressure": service["dependencyPressure"],
                    "criticalIncidents": service["criticalIncidents"],
                    "deployWindowRisk": service["deployWindowRisk"],
                    "verdict": evaluation["verdict"],
                }
            )
        return sorted(rows, key=lambda row: (row["projectedBurnPct"], row["dependencyPressure"]), reverse=True)

    def owner_allocations(self) -> list[dict]:
        buckets: dict[str, list[dict]] = {}
        for row in self.service_catalog():
            buckets.setdefault(row["owner"], []).append(row)
        output: list[dict] = []
        for owner, services in buckets.items():
            output.append(
                {
                    "owner": owner,
                    "serviceCount": len(services),
                    "budgetMinutes": round(sum(item["monthlyBudgetMinutes"] for item in services), 1),
                    "consumedMinutes": round(sum(item["consumedMinutes"] for item in services), 1),
                    "projectedOverrunMinutes": round(sum(item["projectedOverrunMinutes"] for item in services), 1),
                    "averageProjectedBurnPct": round(mean(item["projectedBurnPct"] for item in services), 1),
                }
            )
        return sorted(output, key=lambda row: (row["projectedOverrunMinutes"], row["averageProjectedBurnPct"]), reverse=True)

    def sample_payload(self) -> dict:
        catalog = self.service_catalog()
        return {
            "dashboard": self.summary(),
            "highestRiskService": catalog[0],
            "allocationQueue": self.allocation_queue(),
            "ownerAllocations": self.owner_allocations(),
        }

    def _evaluations(self) -> list[dict]:
        return [self._evaluate_service(service) for service in self.services]

    def _evaluate_service(self, service: dict) -> dict:
        budget = service["monthlyBudgetMinutes"]
        consumed = service["consumedMinutes"]
        projected = service["projectedConsumedMinutes"]
        burn_pct = round((consumed / budget) * 100, 1)
        projected_pct = round((projected / budget) * 100, 1)
        remaining = round(max(0.0, budget - consumed), 1)
        projected_overrun = round(max(0.0, projected - budget), 1)

        risk_score = 18
        if burn_pct >= 85:
            risk_score += 25
        elif burn_pct >= 65:
            risk_score += 15
        elif burn_pct >= 45:
            risk_score += 8

        if projected_pct >= 120:
            risk_score += 22
        elif projected_pct >= 100:
            risk_score += 15
        elif projected_pct >= 80:
            risk_score += 8

        if service["dependencyPressure"] >= 80:
            risk_score += 12
        elif service["dependencyPressure"] >= 60:
            risk_score += 8
        elif service["dependencyPressure"] >= 40:
            risk_score += 4

        if service["criticalIncidents"] >= 2:
            risk_score += 10
        elif service["criticalIncidents"] == 1:
            risk_score += 5

        if service["changeFailureRatePct"] >= 20:
            risk_score += 10
        elif service["changeFailureRatePct"] >= 10:
            risk_score += 5

        if service["deployWindowRisk"] == "high":
            risk_score += 10
        elif service["deployWindowRisk"] == "medium":
            risk_score += 5

        if service["lastRecoveryDrillDays"] > 90:
            risk_score += 7
        elif service["lastRecoveryDrillDays"] > 45:
            risk_score += 3

        risk_score = min(100, risk_score)

        if projected_pct >= 120 or burn_pct >= 90 or risk_score >= 80:
            verdict = "breach"
            next_action = "Freeze the riskiest deploys, borrow healthy budget headroom, and gate changes behind an error-budget review."
        elif projected_pct >= 90 or burn_pct >= 60 or risk_score >= 55:
            verdict = "watch"
            next_action = "Tighten rollout gates, pre-allocate shared budget, and watch dependency pressure before the month-end burn spikes."
        else:
            verdict = "healthy"
            next_action = "Preserve the current budget lane and keep surplus minutes available for shared-service coverage."

        budget_shift = round(projected_overrun if projected_overrun > 0 else max(0.0, (projected - consumed) * 0.2), 1)
        return {
            "serviceId": service["serviceId"],
            "riskScore": risk_score,
            "burnPct": burn_pct,
            "projectedBurnPct": projected_pct,
            "remainingMinutes": remaining,
            "projectedOverrunMinutes": projected_overrun,
            "budgetShiftMinutes": budget_shift,
            "verdict": verdict,
            "topConcern": self._top_concern(service, burn_pct, projected_pct),
            "nextAction": next_action,
        }

    def _top_concern(self, service: dict, burn_pct: float, projected_pct: float) -> str:
        if projected_pct >= 120:
            return "Projected burn is set to blow through the monthly budget before the window closes."
        if burn_pct >= 85:
            return "The live burn rate is already too close to the monthly ceiling."
        if service["dependencyPressure"] >= 80:
            return "Shared dependencies are amplifying the service's budget burn."
        if service["changeFailureRatePct"] >= 20:
            return "Change failure rate is too high for the current deployment pace."
        if service["criticalIncidents"] >= 1:
            return "Recent critical incidents are consuming budget faster than the lane can recover."
        return "The service is still stable, but the budget lane should stay reviewable."

    def _lead_recommendation(self, evaluations: list[dict]) -> str:
        breach = [item for item in evaluations if item["verdict"] == "breach"]
        if breach:
            return "Reassign surplus budget from healthy services before the highest-burn lane forces a freeze under pressure."
        watch = [item for item in evaluations if item["verdict"] == "watch"]
        if watch:
            return "Use shared headroom to protect tier-0 services and tighten deploy gates before projected burn crosses the line."
        return "The current fleet has enough headroom to absorb one more incident without tripping a budget freeze."

    def _source_candidates(self, target_service_id: str) -> list[dict]:
        candidates = []
        for row in self.service_catalog():
            if row["serviceId"] == target_service_id:
                continue
            if row["verdict"] != "healthy":
                continue
            lendable = round(max(0.0, row["remainingMinutes"] * 0.35), 1)
            if lendable <= 0:
                continue
            candidates.append(
                {
                    "serviceId": row["serviceId"],
                    "name": row["name"],
                    "owner": row["owner"],
                    "lendableMinutes": lendable,
                }
            )
        return sorted(candidates, key=lambda item: item["lendableMinutes"], reverse=True)[:2]


def build_service() -> ErrorBudgetAllocatorService:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return ErrorBudgetAllocatorService(services=payload["services"])
