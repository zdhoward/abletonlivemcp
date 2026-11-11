# Probe evidence

One file per probe, `P-NN.md`, written by `scripts/live_probe_run.py P-NN` (T-003). Verdicts are
`go`, `no-go` or `gated` (plan section 4). Owner paths are replaced with `~` before writing.

To run a probe:

1. Add `"dev_probes": true` to the private bridge config (`~/.abletonlivemcp/bridge.json`). Without
   it, every probe method is refused (`dev_probes_disabled`) and the runner exits 2.
2. Behavioural (write) probes also need `"read_only": false`. They run under the lease and touch
   only scratch tracks and scenes they create, which are deleted afterwards.
3. Reinstall the Remote Script (`abletonlivemcp-install`) and reload Live after probe code changes.

P-01 also writes the API dump `docs/data/live-<major>.<minor>-api.json`. Probes are never MCP tools.
Remove `dev_probes` from the config when you are done.
