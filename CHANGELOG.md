# Changelog

All notable changes to this project are tracked here as an engineering log.

## [1.0.0] - 2026-05-14

### Shipped
- Published **error-budget-allocator** as a public Python and FastAPI reliability control surface for allocating error-budget burn across services, dependencies, and deployment windows.
- Added operator-facing HTML views for overview, allocation queue, service matrix, and methodology.
- Added JSON APIs for dashboard summaries, service details, owner allocations, burn matrix records, and sample payloads.
- Added generated SVG proof assets, unit tests, smoke checks, CI, architecture notes, and origin narrative.

## [0.1.0] - 2026-03-11

### Prototype
- Landed the first coherent internal version of the allocator with budget math, forecasted overrun, and ownership-based lending suggestions.
- Introduced the first pass at risk scoring so live burn rate did not overpower dependency pressure and deployment risk.
- Started treating recovery-drill recency as part of operational budget confidence instead of leaving it as separate reliability trivia.

## [Design Phase] - 2025-09-24

### Framing
- Refined the design around a practical operator problem: teams rarely need another burn chart, they need a reliable way to decide who should slow down and who can safely donate headroom.
- Chose FastAPI and a control-plane-style surface so the allocator could read as both an internal product and a reliability workflow primitive.
- Focused the scoring model on questions real SRE and platform teams ask during release pressure: live burn, projected burn, dependency drag, change failure rate, and stale recovery practice.

## [Idea Origin] - 2024-06-18

### Observation
- Noticed the gap between how organizations talk about SLOs and how they actually govern burn during high-change periods.
- Saw that many teams could produce dashboards, but fewer could answer which services deserved budget protection and which lanes should take the operational hit.
- Started sketching a system where budget arbitration would be visible enough for engineering leads, platform owners, and incident commanders to use in the same conversation.

## [Background Signals] - 2023-02-07

### Early signals
- Collected recurring patterns from platform and reliability work where shared services quietly absorbed too much release risk because budget conversations stayed trapped inside individual teams.
- Kept notes on how dependency pressure and change failure rate distorted seemingly healthy services, especially during quarter-end launches and infrastructure migrations.

## [Prehistory] - 2022-10-13

### Foundations
- Logged the first notes around turning reliability posture into an allocation problem instead of only a reporting problem.
- Captured the core idea that error budgets become much more useful when they can explain who should stop, who can lend, and why that decision is defensible in retrospect.
