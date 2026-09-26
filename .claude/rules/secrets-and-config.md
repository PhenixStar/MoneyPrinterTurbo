# Secrets and config rules

- The fork `PhenixStar/MoneyPrinterTurbo` is **public** (GitHub forks of public repos cannot be private).
  Treat every tracked file as published.
- Source of truth for credentials: `~/mapping/mapping-config/services/**/tokens.env` (private repo).
- `config.toml` is gitignored and written with mode 600 by `scripts/sync-config-from-mapping.py`.
  Before any commit, confirm `git status` does not list `config.toml`, `config.toml.bak`, `.run/` or `storage/`.
- Never print, log, or paste a secret value into chat, commit messages, docs or reports — use key names
  and set/missing status only (the sync script already prints only that).
- To add or change a credential: put it in mapping first (e.g. `services/pexels/tokens.env` with
  `PEXELS_API_KEY=`), then add/adjust the entry in `MANAGED` inside the sync script, then re-run it.
- The sync script rewrites only the keys in `MANAGED`; other settings edited through the WebUI are kept.
  Do not hand-edit managed keys in `config.toml` — they will be overwritten on the next sync.

## Current provider mapping

| config key | mapping source |
|------------|----------------|
| `llm_provider` | literal `minimax` (MiniMax-M3) — set **only when config.toml is first created**; change it in the WebUI afterwards |
| `llm_fallback_provider` | literal `openai` (= Z.ai GLM-5.3) — first creation only; retried once when the primary returns an error |
| `ollama_*` | local Ollama `http://127.0.0.1:11434/v1`, model `gemma4:latest` (selectable, not default) |
| `claude_code_cli_path` | local `claude` binary |
| `openai_*` (Z.ai GLM coding plan, `glm-5.3`) | `services/ai-api/z-ai/tokens.env` (`ZAI_CODING_PLAN_API_KEY`, `ZAI_BASE_URL_OPENAI`) — the paas key in `services/z-ai` has no balance |
| `minimax_*`, `[minimax_tts]` | `services/minimax/tokens.env` |
| `moonshot_*` (Kimi) | **not mapped** — `KIMI_API_KEY` returns 401 on `.cn` and `.ai` |
| `gemini_api_key` | `services/talon/tokens.env` → `GEMINI_API_KEY` |
| `openrouter_*` / `groq_api_key` / `grok_api_key` | `services/ai-api/{openrouter,groq,xai}`; OpenRouter model `minimax/minimax-m3` |

| `anthropic_api_key` | `services/hermes/tokens.env` |
| `[elevenlabs] api_key` | `services/elevenlabs/tokens.env` |
| `pexels_api_keys` | `services/pexels/tokens.env` → `PEXELS_API_KEY` |
| `coverr_api_keys` | `services/coverr/tokens.env` → `COVERR_API_KEY` (second video source; Pexels stays default) |
| `pixabay_api_keys` | `services/pixabay/tokens.env` — not configured (optional) |

Verified working 2026-09-27: MiniMax `MiniMax-M3` (primary), Z.ai `glm-5.3` (fallback), Ollama `gemma4:latest`, Groq, OpenRouter, Gemini, Pexels, Coverr.
Validated snapshot of the full `config.toml`: `~/mapping/mapping-config/services/moneyprinter/config.toml` — refresh it after deliberate config changes.
Local-footage mode: clips must live under `storage/local_videos/` (upstream path guard rejects anything else).
