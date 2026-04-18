# Scripts

## `convert_claude_agents_to_codex.py`

Converts Claude-style markdown agents under `plugins/*/agents/*.md` into Codex custom
agent TOML files.

Default behavior:

- reads from `plugins/*/agents/*.md`
- writes generated TOML files to `codex-agents/`
- does not install anything into `~/.codex/agents/`

Examples:

```bash
# Generate repo-local TOML files for review
python3 scripts/convert_claude_agents_to_codex.py

# Preview what would be written
python3 scripts/convert_claude_agents_to_codex.py --dry-run

# Convert only one plugin
python3 scripts/convert_claude_agents_to_codex.py --plugin git

# Later, after pushing or publishing, write directly to the user agent directory
python3 scripts/convert_claude_agents_to_codex.py \
  --output ~/.codex/agents \
  --force

# Map Claude model aliases when needed
python3 scripts/convert_claude_agents_to_codex.py \
  --map-claude-models \
  --output ~/.codex/agents \
  --force
```

## `install_codex_agents.sh`

Installs generated Codex custom agents into `~/.codex/agents/` by calling the
converter script with the repository defaults.

Examples:

```bash
bash scripts/install_codex_agents.sh
bash scripts/install_codex_agents.sh --target ~/.codex/agents --no-model-map
```
