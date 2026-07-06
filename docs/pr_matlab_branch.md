## Summary

Fixes three MATLAB-only issues in `ntrm.m` on a branch based directly on `main`.

This PR is intentionally independent from the Python research-tooling branch so it can be reviewed by a power-systems/MATLAB reviewer without pulling in Python changes.

## Changes

- Corrects branch metric slice assignments so each loop iteration writes a single row of `cen_de_2`.
- Changes random initiating-outage sampling from bus count to branch count.
- Makes `fail_min` an optional argument with the existing default value of `3`.
- Fixes the `Eigenvector` spelling in comments.
- Uses `onCleanup` so `TempTestCase.m` is deleted on exit or error.

## Review Notes

The sampling fix is a semantic change. Any previously published or random-path MATLAB results that depended on `randi(n_bus, [k 1])` should be regenerated.

## Testing

Local MATLAB/AC-CFM execution was not available in this environment.

Recommended reviewer checks:

- Run `ntrm('case39.m', sample_size)` with default `fail_min`.
- Run `ntrm('case39.m', sample_size, 3)` and confirm behavior matches the default.
- Verify sampled initiating contingencies are valid branch rows.
- Confirm `TempTestCase.m` is removed after normal completion and after an induced error.

## Future Work

- Add regression output from a MATLAB/AC-CFM environment.
- Compare affected sampling results against any previously reported NTRM MATLAB outputs.
