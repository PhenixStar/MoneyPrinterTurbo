# Process and port rules

- Fixed ports: API `8080` (from `config.toml` `listen_port`), WebUI `8501`. Do not change or increment them.
- Exposure (owner decision 2026-09-27: network-wide): WebUI binds `0.0.0.0` by default (`MPT_HOST=127.0.0.1`
  restricts it). Its Settings dialog shows (and has a Key Backup tab exporting) every API key, so reach is
  limited by ufw: `8501`/`8080` allowed from `10.3.1.0/24` only; Tailscale passes via `ts-input`.
  Never add an `Anywhere` ufw rule for these ports.
  `hide_config` is obsolete upstream (the dialog resets it to false) — do not rely on it.
  The API follows `listen_host` (upstream default `0.0.0.0`, no API key) — trusted network only.
- Start/stop only through `scripts/moneyprinter-service.sh {start|stop|restart|status} [api|webui|all]`.
  It records PIDs in `.run/*.pid` and logs in `.run/*.log`.
- Do not run `webui.sh` / `webui.bat`: upstream's launcher silently moves to 8502+ when 8501 is busy,
  which creates ghost instances.
- On "port in use": run `scripts/moneyprinter-service.sh status` and `ss -ltnp 'sport = :PORT'`.
  If the owner is our stale PID, stop it via the script; if it is someone else's process, ask the owner.
- Anything started for a test or verification must be stopped at the end of that task.
- Heavy jobs: `max_concurrent_tasks` in `config.toml` caps parallel renders. The box shares RAM with
  Ollama models, so keep it low (≤ 2) when a large local model is loaded.
- Local LLM is the shared Ollama service on `:11434` — never stop or restart it from this project.
