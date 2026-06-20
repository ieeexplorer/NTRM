# Sussex PhD research extension

> **Independent research prototype.** This fork explores methods aligned with
> the theme *Artificial Intelligence and Agent-based Control for Improving
> Energy Network Resilience to Threats*. It is not an official University of
> Sussex, NESO, or electricity-operator tool.

The extension connects three reproducible modules while preserving the original
MATLAB NTRM implementation:

| Module | Purpose |
|---|---|
| [`cascade_ml`](cascade_ml/) | DC cascade surrogate, scenario generation, graph features, ML baselines, and an executable AC-CFM comparison protocol. |
| [`agent_control`](agent_control/) | Network-aware coordination of flexible load, batteries, and generators with paired control and sensitivity experiments. |
| [`data_pipeline`](data_pipeline/) | Provenance-preserving NESO snapshots mapped to bounded synthetic IEEE test-case conditions for conditional screening. |

The technical roadmap is documented in
[`docs/research_roadmap.md`](docs/research_roadmap.md). Discussion with the NTRM
maintainers is tracked in
[`sskazakos/NTRM#1`](https://github.com/sskazakos/NTRM/issues/1).

## Run the integrated demonstration

After installing the development environment, the default command uses a
committed NESO snapshot so the output is reproducible and works offline:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python run_demo.py
```

Use `python run_demo.py --live` to fetch the latest valid actual NESO demand
record. Add `--model PATH` only when a trained model appropriate to the mapped
operating range is available. Without one, the demo does not invent a risk
probability.

## Evidence status

- Unit and integration tests verify software behaviour on controlled cases.
- Public NESO data parameterises a synthetic IEEE 39-bus scenario; it does not
  reconstruct the GB network.
- DC results have not yet been validated against paired AC-CFM runs.
- Generated model metrics, intervention benefits, and cost assumptions are not
  presented as research findings until their experiments are reproduced and
  reviewed.

# Original Network Theory Resilience Metric (NTRM)
The Network Theory Resilience Metric (NTRM) samples cascade scenarios from 
a MATPOWER case file, then runs the AC Cascading Failure Model (AC-CFM) code,
for all the resulting cases. Then, a set of network science metrics for the
network under study are derived, using MATLAB and BCT functions. The following
parameters are calculated:

- Degree centrality of each node (bus)
- Eigenvecor centrality of each node (bus)
- Betweenness centrality of each node (bus)
- Closeness centrality of each node (bus)
- Clustering coefficient of each node (bus)
- Self-admittance of each bus
- Edge betweenness centrality for each edge (branch)
- [Degree of node(i) * Degree of node(j)] for each edge (branch)
- Total load shedding each branch causes in all scenarios
- Total amount of times each branch contributed to a cascade

# Prerequisites:
- Matlab R2020b or later (but may work with earlier versions)
- Matpower 7.1 or later
    https://matpower.org/, or https://github.com/MATPOWER/matpower
- AC-CFM and its prerequisites
    https://github.com/mnoebels/AC-CFM, Reference: Noebels, M.,
    Preece, R., Panteli, M. "AC Cascading Failure Model for
    Resilience Analysis in Power Networks." IEEE Systems Journal (2020).
- Brain Connectivity Toolbox (BCT)
    https://sites.google.com/site/bctnet/home, Reference: Rubinov M,
    Sporns O, "Complex network measures of brain connectivity:
    Uses and interpretations", (2010) NeuroImage 52:1059-69.

# Usage
```
ntrm('MATPOWER case file name', [sample size])
```

e.g.  results = ntrm('case39', 500)

# Extension modules

The [`cascade_ml`](cascade_ml/) directory contains a tested Python DC
power-flow surrogate, reproducible contingency generator, feature pipeline, and
baseline machine-learning workflow. It is intended for preliminary research and
validation against NTRM/AC-CFM, not as an AC-CFM replacement.

The [`agent_control`](agent_control/) directory adds constrained flexible-load,
battery, and generator agents with network-aware centralised and auction control
experiments. Preventive intervention is reported separately from involuntary
blackout loss.

The [`data_pipeline`](data_pipeline/) directory ingests reproducible public NESO
demand snapshots, maps them to bounded synthetic IEEE test-case conditions, and
screens conditional contingencies. It is explicitly a research demonstrator,
not a representation of the live GB network or operational advice.

# Acknowledgements
The authors would like to thank Mathaios Panteli for valuable discussions
and support. This work was supported by the Engineering and Physical
Sciences Research Council [EP/W034204/1]
