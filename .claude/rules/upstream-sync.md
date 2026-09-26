# Upstream sync rules

Remotes: `origin` = PhenixStar fork, `upstream` = harry0703/MoneyPrinterTurbo.

```bash
git fetch upstream
git merge --ff-only upstream/main || git merge upstream/main   # resolve conflicts, keep local files
uv sync                                                          # deps may have changed
python3 scripts/sync-config-from-mapping.py --dry-run            # detect renamed/removed config keys
scripts/moneyprinter-service.sh restart
git push origin main
```

- Keep fork changes **additive**: new files under `scripts/`, `.claude/`, `CLAUDE.md`, `plans/`, and
  `.gitignore` lines. Avoid editing upstream `app/` or `webui/` code unless fixing a real bug; if you do,
  prefer sending it upstream as a PR.
- After a sync, any `key-not-in-config` line from the sync script's dry run means upstream renamed a
  key — update `MANAGED` in `scripts/sync-config-from-mapping.py`.
- New keys that upstream adds to `config.example.toml` are NOT auto-added to an existing `config.toml`;
  compare with `diff <(grep -oE '^[a-z_]+' config.example.toml | sort -u) <(grep -oE '^[a-z_]+' config.toml | sort -u)`.
