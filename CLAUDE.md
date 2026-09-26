# CLAUDE.md — MoneyPrinterTurbo (PhenixStar fork)

Local install of [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo): topic → LLM script →
stock/AI footage → TTS voice-over → subtitles → rendered short video. English docs: `README-en.md`.

## Repo layout that matters

| Path | Role |
|------|------|
| `origin` | `github.com/PhenixStar/MoneyPrinterTurbo` — **public** fork |
| `upstream` | `github.com/harry0703/MoneyPrinterTurbo` |
| `app/` | FastAPI backend (`main.py` → `app.asgi:app`), services in `app/services/` |
| `webui/Main.py` | Streamlit UI |
| `app/models/llm_provider.py` | LLM provider registry (default base URLs / models) |
| `config.toml` | Runtime config — **gitignored, holds secrets, mode 600** |
| `scripts/sync-config-from-mapping.py` | Fills `config.toml` from the private mapping repo |
| `scripts/moneyprinter-service.sh` | start / stop / status on fixed ports |
| `.run/` | PID files + logs (gitignored) |
| `storage/` | Task outputs (videos) |

## Everyday commands

```bash
uv sync                                        # install / update deps (.venv, Python 3.11)
python3 scripts/sync-config-from-mapping.py    # (re)render secrets into config.toml
scripts/moneyprinter-service.sh start          # API :8080 + WebUI :8501
scripts/moneyprinter-service.sh status
scripts/moneyprinter-service.sh stop
```

## Rules (details in `.claude/rules/`)

1. **Secrets** — `.claude/rules/secrets-and-config.md`. This fork is public. No key ever goes in git.
   `config.toml` is the only place secrets live on disk here; the source of truth is
   `~/mapping/mapping-config/services/**/tokens.env`. Never print secret values.
2. **Processes** — `.claude/rules/process-and-ports.md`. Fixed ports 8080/8501, managed via the service
   script. Never use `webui.sh` (it hops ports), never spawn duplicates, stop what you start.
3. **Upstream sync** — `.claude/rules/upstream-sync.md`. Keep local changes small and additive so
   `git merge upstream/main` stays clean.
4. **Platform** — this box is aarch64 (NVIDIA GB10). Whisper runs on CPU (`[whisper] device="cpu"`);
   `subtitle_provider="edge"` keeps whisper off the critical path.
5. Commits: conventional commits, no AI attribution, never `config.toml` / `.run/` / `storage/`.
