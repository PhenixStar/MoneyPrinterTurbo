# Process and port rules

- Fixed ports: API `8080` (from `config.toml` `listen_port`), WebUI `8501`. Do not change or increment them.
- Exposure: WebUI binds `127.0.0.1` by default. LAN access is opt-in via `MPT_HOST=0.0.0.0` and only
  with `hide_config = true` in `config.toml` (otherwise the settings panel shows every API key).
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
