# AC-CFM validation protocol

The DC surrogate is not considered validated until identical contingencies have
been executed in NTRM/AC-CFM and compared. This directory intentionally contains
no invented AC-CFM output or placeholder performance result.

## Required paired schema

Export one row per scenario from each model:

```text
contingency_key,final_unserved_mw,severe_event
0|5,125.0,0
2|17,1800.0,1
```

`contingency_key` must use the same stable, zero-based MATPOWER branch-row IDs in
both files. The severe-event threshold must also be identical and documented.

## Case39 N-1 AC-CFM fixture

The placeholder JSON schema lives at
`tests/fixtures/case39_ac_cfm_n1_schema.json`. It is intentionally empty until a
MATLAB reviewer confirms the exact AC-CFM entry point and generates real output.

When populated, the fixture should contain all 46 case39 single-branch
contingencies. Use zero-based Python branch IDs as the canonical key and include
the one-based MATLAB row as `matlab_branch_row` for cross-reference. Each row
should include:

- `branch_idx`;
- `matlab_branch_row`;
- `from_bus`;
- `to_bus`;
- `ac_branch_loadings_mw`;
- `ac_cascade_flag`;
- `ac_unserved_mw`.

The accompanying tests validate the schema today and skip the populated-fixture
checks until the `contingencies` array contains real AC-CFM results.

## Suggested experiment

1. Fix the MATPOWER case, operating point, contingency list, protection/settings,
   and severe-event threshold.
2. Generate at least 100 unique N-2 contingencies with a recorded seed.
3. Run the list through this DC surrogate.
4. Run the same list through NTRM/AC-CFM in MATLAB.
5. Export scenario-level final load shedding from AC-CFM.
6. Compare the files:

```powershell
python scripts/validate_vs_acfm.py `
  --dc data/dc_results.csv `
  --acfm validation_results/acfm_results.csv
```

The command reports matched scenarios, MAE, RMSE, bias, classification
agreement, and false-positive/false-negative rates. Failed AC-CFM convergence
must be retained as a separate status and excluded transparently rather than
silently converted to zero load shedding.

## Interpretation

Agreement is not assumed. DC power flow omits reactive power, voltage collapse,
losses, and detailed protection behaviour. The comparison should identify the
operating conditions and contingency types for which the surrogate is useful,
not merely seek one favourable headline number.
