# Research-extension roadmap

## Motivation

Cascading failures couple network topology, operating state, protection, and
resource response. This prototype investigates whether fast surrogate models
can screen contingencies and whether constrained distributed resources can
reduce simulated consequences. It is designed to create testable research
questions, not to claim readiness for operational deployment.

## Research questions

1. Under which operating conditions and contingency types does a DC cascade
   surrogate reproduce AC-CFM load-shedding severity and event classification?
2. Which pre-contingency graph and loading features generalise across operating
   points without leakage between related contingencies?
3. When does risk-gated resource coordination outperform always-active and
   no-control baselines after intervention cost and preventive curtailment are
   included?
4. How sensitive are conclusions to battery power/energy, generator ramping,
   flexible-load availability, severe-event thresholds, and prediction errors?

## Current prototype

- Phase 1 provides a unit-correct DC power-flow cascade surrogate, reproducible
  scenarios, features, and transparent ML baselines.
- Phase 2 compares no-control, centralised, auction, and risk-gated resource
  coordination while separating preventive curtailment from involuntary loss.
- Phase 3 ingests provenance-preserving public NESO demand snapshots and maps a
  bounded demand multiplier onto an IEEE 39-bus research case.

## Validation gates

1. Validate base-case DC branch flows against MATPOWER/PYPOWER.
2. Run identical contingencies through DC and AC-CFM and report paired MAE,
   bias, classification agreement, and false-positive/negative rates.
3. Train across multiple operating points and reserve untouched contingency
   groups for final evaluation.
4. Compare agent control with no-control and centralised baselines on identical
   scenarios, including intervention cost and unnecessary activation.
5. Repeat results across resource and threshold sensitivity configurations.

## Future extensions

- Regional or openly licensed distribution-network models in place of national
  aggregate-to-IEEE proxy mapping.
- Weather and hazard scenarios with explicit spatial and temporal alignment.
- Multi-layer dependencies only after electrical-network validation is sound.
- Time-series storage state, recovery, and energy-not-served metrics.
- Uncertainty calibration and decision thresholds based on stated loss models.

These are research directions, not implemented capabilities or application
claims. A personal proposal and literature review should be added only after
their wording and citations have been reviewed by the author.
