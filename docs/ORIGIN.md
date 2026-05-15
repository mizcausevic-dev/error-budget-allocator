# Why We Built This

**error-budget-allocator** started from a reliability planning problem that shows up long after teams say they have an SLO program in place. Most organizations can tell you what their target is and how much budget is left in theory. Far fewer can tell you what to do next when several services are burning at once, when one team wants to keep shipping, and when a shared dependency is quietly making everyone else less safe.

At enterprise scale, the real problem is not the absence of metrics. It is the absence of arbitration. One service starts running hot, another has extra headroom, a tier-0 path is entering a risky deployment window, and a platform lead has to decide whether to let the train keep moving or start pulling brakes. Those decisions usually happen in a rush, with one dashboard for burn, another for incidents, another for deployments, and no single place that explains which service should receive protection and which one can afford to give some up.

Existing reliability tooling often stops one step too early. It is good at reporting budget burn, service health, and post-incident evidence. It is weaker at turning that into an operator-grade budget allocation view. Most tools can tell you which lane is unhealthy. They do not help you reason about whether to shift headroom from a healthier service, whether dependency pressure should count against a service that looks fine in isolation, or whether a change window should be slowed before the budget breach becomes obvious to everyone else.

We built **error-budget-allocator** to model that decision layer directly. The design philosophy is simple:

- **operator-first**
  The output should help a reliability lead act, not just observe.
- **reliability-legible**
  Burn, overrun, dependency pressure, incident counts, and change risk should live in the same frame.
- **CI-ready**
  The same logic should be usable in release gates, review workflows, or planning loops without being rewritten.

That is why the repo does more than compute percentages. It produces an allocation queue, suggests budget shifts, highlights likely donor lanes, and keeps the narrative around the risk close to the math. The goal is to make budget pressure reviewable before it turns into an argument during a live change or an incident retrospective.

What comes next is predictable and useful. The roadmap includes live scenario simulation for release windows, richer dependency blast-radius weighting, and export paths into broader SRE or platform-governance systems. The long-term value of **error-budget-allocator** is not that it invents a new reliability metric. It gives teams a more operational way to use the metrics they already claim to trust.
