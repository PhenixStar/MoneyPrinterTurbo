# MoneyPrinterTurbo — Pexels, MiniMax→GLM fallback, final config (2026-09-27)

## Outcome
Topic-only video generation works end to end: "why the ocean is salty" → MiniMax-M3 script →
8 Pexels clips → edge-tts voice → subtitles → 1080x1920, 49.7 s MP4 in 203 s.

## Changes
- Pexels key stored in mapping `services/pexels/tokens.env` (+ `README.md`); validated HTTP 200, 25,000 req/month.
- New `llm_fallback_provider` setting: `_generate_response` retries once with the fallback provider when the
  primary returns an `Error:` string. Primary `minimax`, fallback `openai` (Z.ai GLM-5.3).
  Forced-failure test (invalid MiniMax key) returned the GLM answer. 4 new unit tests, plus `test/conftest.py` so a local fallback setting never leaks live calls into unit tests. Full suite: 1318 passed, 0 failed.
- Sync script: default provider `minimax` + fallback on first create; inserts keys missing from an older `config.toml`.
- Validated `config.toml` snapshot saved to mapping `services/moneyprinter/config.toml` (mode 600).
- API stays network-wide on `0.0.0.0:8080` (owner decision); WebUI stays `127.0.0.1:8501` with `hide_config = true`.

## Unresolved questions
- None blocking. WebUI LAN exposure remains opt-in via `MPT_HOST=0.0.0.0`.
