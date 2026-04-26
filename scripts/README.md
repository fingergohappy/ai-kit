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

It does not write user-level skill symlinks by default. Plugin-bundled skills
are exposed by installing the plugins in Codex. Use `--link-skills` only when
you explicitly want `~/.agents/skills/` symlinks.

Examples:

```bash
bash scripts/install_codex_agents.sh
bash scripts/install_codex_agents.sh --target ~/.codex/agents --no-model-map
bash scripts/install_codex_agents.sh --link-skills
bash scripts/install_codex_agents.sh --skills-target ~/.agents/skills --link-skills
```

## `install_codex_plugins.sh`

Installs this repository's Codex plugins into the user's personal Codex plugin
directory, merges the personal marketplace metadata, then calls
`install_codex_agents.sh` to install bundled custom agents.

Default behavior:

- scans `plugins/*/.codex-plugin/plugin.json`
- copies plugin directories to `~/.codex/plugins/`
- creates or updates `~/.agents/plugins/marketplace.json`
- installs custom agents into `~/.codex/agents/`
- does not write `~/.agents/skills/` unless `--link-skills` is passed

Examples:

```bash
bash scripts/install_codex_plugins.sh
bash scripts/install_codex_plugins.sh --no-agents
bash scripts/install_codex_plugins.sh --link-skills
bash scripts/install_codex_plugins.sh \
  --plugins-target ~/.codex/plugins \
  --marketplace ~/.agents/plugins/marketplace.json
```

## `test_install_codex_plugins.sh`

Runs an integration test for `install_codex_plugins.sh` using a temporary
`HOME`, so it does not modify the caller's Codex configuration.

```bash
bash scripts/test_install_codex_plugins.sh
```
