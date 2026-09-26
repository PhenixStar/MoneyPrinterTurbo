#!/usr/bin/env python3
"""
Render MoneyPrinterTurbo's config.toml from the mapping-config credential store.

Why this exists:
  This repo is a PUBLIC fork, so no secret may ever be committed here. Secrets
  live in the private mapping repo (~/mapping/mapping-config/services/**/tokens.env).
  This script copies the needed values into the gitignored config.toml.

Behaviour:
  - If config.toml is missing it is created from config.example.toml.
  - Only the keys listed in MANAGED are rewritten; every other setting (including
    anything changed through the web UI) is left untouched.
  - Secret values are never printed; only key names and "set"/"missing" status.

Usage:
  python3 scripts/sync-config-from-mapping.py [--dry-run] [--mapping DIR]
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.toml"
EXAMPLE = ROOT / "config.example.toml"
DEFAULT_MAPPING = Path.home() / "mapping" / "mapping-config" / "services"

# Default LLM: MiniMax-M3 (owner's choice), falling back to Z.ai GLM (the
# "openai" slot below) when MiniMax errors. Local Ollama stays configured too.
DEFAULT_LLM_PROVIDER = "minimax"
DEFAULT_LLM_FALLBACK_PROVIDER = "openai"
DEFAULT_OLLAMA_MODEL = "gemma4:latest"

# Written only when config.toml is first created, so a provider chosen later
# in the web UI is never reverted by a re-sync.
INITIAL = {
    ("app", "llm_provider"): ("lit", DEFAULT_LLM_PROVIDER),
    ("app", "llm_fallback_provider"): ("lit", DEFAULT_LLM_FALLBACK_PROVIDER),
}

# (section, key) -> value source, rewritten on every run.
#   ("env", "relative/tokens.env", "VAR")  -> read secret from mapping
#   ("lit", value)                         -> literal (non-secret) value
# A key whose source resolves to empty is left unchanged in config.toml.
MANAGED = {
    # Local Ollama (OpenAI-compatible endpoint)
    ("app", "ollama_base_url"): ("lit", "http://127.0.0.1:11434/v1"),
    ("app", "ollama_model_name"): ("lit", DEFAULT_OLLAMA_MODEL),
    # Claude Code CLI adapter (uses the logged-in local `claude` binary)
    ("app", "claude_code_cli_path"): ("lit", shutil.which("claude") or ""),
    # Z.ai GLM (coding plan — the pay-as-you-go paas key has no balance)
    # through the generic OpenAI-compatible slot
    ("app", "openai_api_key"): ("env", "ai-api/z-ai/tokens.env", "ZAI_CODING_PLAN_API_KEY"),
    ("app", "openai_base_url"): ("env", "ai-api/z-ai/tokens.env", "ZAI_BASE_URL_OPENAI"),
    ("app", "openai_model_name"): ("lit", "glm-5.3"),
    # MiniMax (LLM + TTS share one key)
    ("app", "minimax_api_key"): ("env", "minimax/tokens.env", "MINIMAX_API_KEY"),
    ("app", "minimax_base_url"): ("env", "minimax/tokens.env", "MINIMAX_BASE_URL"),
    ("app", "minimax_model_name"): ("env", "minimax/tokens.env", "MINIMAX_MODEL"),
    ("minimax_tts", "api_key"): ("env", "minimax/tokens.env", "MINIMAX_API_KEY"),
    ("minimax_tts", "base_url"): ("env", "minimax/tokens.env", "MINIMAX_API_HOST"),
    # Kimi / Moonshot intentionally not mapped: KIMI_API_KEY returns 401 on both
    # api.moonshot.cn and api.moonshot.ai (checked 2026-09-26).
    # Gemini
    ("app", "gemini_api_key"): ("env", "talon/tokens.env", "GEMINI_API_KEY"),
    # OpenRouter / Groq / xAI Grok
    ("app", "openrouter_api_key"): ("env", "ai-api/openrouter/tokens.env", "OPENROUTER_API_KEY"),
    # upstream default "minimax/minimax-m3:free" no longer exists on OpenRouter
    ("app", "openrouter_model_name"): ("lit", "minimax/minimax-m3"),
    ("app", "groq_api_key"): ("env", "ai-api/groq/tokens.env", "GROQ_API_KEY"),
    ("app", "grok_api_key"): ("env", "ai-api/xai/tokens.env", "XAI_API_KEY"),
    # Anthropic API (optional; empty in mapping today)
    ("app", "anthropic_api_key"): ("env", "hermes/tokens.env", "ANTHROPIC_API_KEY"),
    # ElevenLabs TTS / music
    ("elevenlabs", "api_key"): ("env", "elevenlabs/tokens.env", "ELEVENLABS_API_KEY"),
    # Stock footage sources (pick one per video in the WebUI "Video Source").
    # Pexels and Coverr are configured; Pixabay is optional (add
    # services/pixabay/tokens.env PIXABAY_API_KEY and re-run).
    ("app", "pexels_api_keys"): ("env-list", "pexels/tokens.env", "PEXELS_API_KEY"),
    ("app", "pixabay_api_keys"): ("env-list", "pixabay/tokens.env", "PIXABAY_API_KEY"),
    ("app", "coverr_api_keys"): ("env-list", "coverr/tokens.env", "COVERR_API_KEY"),
}

SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def read_env(path: Path) -> dict:
    """Parse a KEY=VALUE file; tolerates quotes, comments and `export`."""
    values = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.removeprefix("export ").partition("=")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        values[key.strip()] = val
    return values


def resolve(source, mapping_dir: Path, cache: dict):
    """Return the TOML literal for a source, or None when it resolves empty."""
    kind = source[0]
    if kind == "raw":  # already a TOML literal (booleans, numbers)
        return source[1]
    if kind == "lit":
        return json.dumps(source[1]) if source[1] else None
    rel, var = source[1], source[2]
    if rel not in cache:
        cache[rel] = read_env(mapping_dir / rel)
    raw = cache[rel].get(var, "").strip()
    if not raw:
        return None
    if kind == "env-list":
        return json.dumps([v.strip() for v in raw.split(",") if v.strip()])
    return json.dumps(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.mapping.is_dir():
        print(f"mapping services dir not found: {args.mapping}", file=sys.stderr)
        return 1
    sources = dict(MANAGED)
    if not CONFIG.exists():
        shutil.copyfile(EXAMPLE, CONFIG)
        print("created config.toml from config.example.toml")
        sources.update(INITIAL)

    cache: dict = {}
    wanted = {k: resolve(v, args.mapping, cache) for k, v in sources.items()}

    lines = CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
    section, done = "", set()
    for i, line in enumerate(lines):
        m = SECTION_RE.match(line)
        if m:
            section = m.group(1).strip()
            continue
        km = re.match(r"^(\s*)([A-Za-z0-9_]+)(\s*=\s*)(.*?)(\s*#.*)?$", line.rstrip("\n"))
        if not km:
            continue
        key = (section, km.group(2))
        if key in wanted and wanted[key] is not None:
            comment = km.group(5) or ""
            lines[i] = f"{km.group(1)}{km.group(2)}{km.group(3)}{wanted[key]}{comment}\n"
            done.add(key)

    # Keys absent from an older config.toml (e.g. added upstream later) are
    # inserted right after their [section] header.
    for key, val in wanted.items():
        if key in done or val is None:
            continue
        for i, line in enumerate(lines):
            m = SECTION_RE.match(line)
            if m and m.group(1).strip() == key[0]:
                lines.insert(i + 1, f"{key[1]} = {val}\n")
                done.add(key)
                break

    for key, val in sorted(wanted.items()):
        status = "set" if key in done else ("missing-in-mapping" if val is None else "section-not-in-config")
        print(f"  [{key[0]}] {key[1]:<24} {status}")

    if args.dry_run:
        print("dry run: config.toml not written")
        return 0
    CONFIG.write_text("".join(lines), encoding="utf-8")
    os.chmod(CONFIG, 0o600)  # holds secrets
    print(f"wrote {CONFIG} (mode 600)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
