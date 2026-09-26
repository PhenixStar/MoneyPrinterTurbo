# MoneyPrinterTurbo fork + install — report (2026-09-26)

## Outcome
MoneyPrinterTurbo v1.3.7 is forked to `PhenixStar/MoneyPrinterTurbo`, installed in
`~/projects/moneyprinter-video` (uv venv, Python 3.11, aarch64), and configured from the mapping repo.
A full video render was verified end to end. Services are stopped (start with `scripts/moneyprinter-service.sh start`).

## Verified
- API `:8080/docs` and WebUI `:8501` return 200.
- Script generation through local Ollama `gemma4:latest` (~22 s); search terms relevant when a script is passed.
- edge-tts voice-over, subtitle SRT, and a 1080x1920 MP4 with burned-in subtitles (22 s render, local-footage mode).
- Cloud LLM keys: Z.ai `glm-5.3` (coding plan), MiniMax `MiniMax-M3`, Groq, OpenRouter `minimax/minimax-m3`, Gemini → HTTP 200.
- WebUI binds `127.0.0.1` only; fresh config gets `hide_config = true`; re-sync leaves `llm_provider`/`hide_config` alone.
- All deps import on aarch64, including `azure-cognitiveservices-speech` and `faster-whisper`.

## Added to the fork (uncommitted)
- `scripts/sync-config-from-mapping.py` — renders secrets into gitignored `config.toml` (mode 600); rewrites only managed keys so WebUI edits survive.
- `scripts/moneyprinter-service.sh` — start/stop/status on fixed ports with PID files in `.run/`; refuses to touch foreign port owners.
- `CLAUDE.md` + `.claude/rules/{secrets-and-config,process-and-ports,upstream-sync}.md`.
- `.gitignore`: `/.run/`, `/.agentkit/`.

## Mapping repo (edited, uncommitted — multi-machine repo)
- New `services/moneyprinter/README.md` (credential routes + live-check status).
- New `<!-- SECTION: moneyprinter -->` in `roadmap-ai-read.md` (MP1 done, MP2–MP4 pending).

## Findings
- The `services/z-ai` paas key returns 429 "insufficient balance"; the coding-plan key in `ai-api/z-ai` works.
- `KIMI_API_KEY` returns 401 on both Moonshot hosts; left unmapped.
- Upstream `webui.sh` moves to 8502+ when 8501 is busy; the rules forbid using it.
- API listens on `0.0.0.0` with no API key (upstream default); fine on a trusted LAN only.
- Gemini key is read from `services/talon` (`GEMINI_API_KEY`) so no personal handle appears in the public fork.
- Local clips must live under `storage/local_videos/` (upstream path guard).

## Unresolved questions
1. No Pexels/Pixabay key exists in mapping. Should I register a free Pexels key, or will you add `services/pexels/tokens.env`? Without it, topic→video needs local clips.
2. Commit and push the fork-local files to `origin` (public; checked free of secrets and personal handles), and commit the mapping-repo changes?
3. Keep `ollama`/`gemma4` as the default LLM, or switch the default to Z.ai `glm-5.3` / MiniMax-M3?
4. Should the API also bind to `127.0.0.1` (`listen_host`), or stay LAN-reachable?
