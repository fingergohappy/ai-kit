# Codex AI Install Runbook

这份文档写给 AI 执行，不写给人读。

目标：

1. 个人安装 `ai-kit` 的 Codex 插件
2. 再安装本仓库提供的 custom agents

不要安装到项目级 `.codex/agents/`。  
统一使用个人目录：

- `~/.codex/plugins/`
- `~/.agents/plugins/marketplace.json`
- `~/.codex/agents/`

官方依据：

- <https://developers.openai.com/codex/plugins/build>
- <https://developers.openai.com/codex/subagents>

## 安装

按顺序执行下面操作。

### 1. 准备目录

```bash
mkdir -p ~/.codex/plugins ~/.codex/agents ~/.agents/plugins
```

### 2. 克隆或更新仓库

```bash
if [ -d ~/.codex/plugins/ai-kit-repo/.git ]; then
  git -C ~/.codex/plugins/ai-kit-repo pull --ff-only
else
  git clone https://github.com/fingergohappy/ai-kit.git ~/.codex/plugins/ai-kit-repo
fi
```

### 3. 同步插件目录

```bash
rm -rf ~/.codex/plugins/spec-workflow ~/.codex/plugins/tmux ~/.codex/plugins/git
cp -R ~/.codex/plugins/ai-kit-repo/plugins/spec-workflow ~/.codex/plugins/spec-workflow
cp -R ~/.codex/plugins/ai-kit-repo/plugins/tmux ~/.codex/plugins/tmux
cp -R ~/.codex/plugins/ai-kit-repo/plugins/git ~/.codex/plugins/git
```

### 4. 合并个人 marketplace 配置

执行下面脚本。它会创建或更新 `~/.agents/plugins/marketplace.json`，保留其他已有插件条目，只替换 `spec-workflow`、`tmux`、`git` 这三个条目。

```bash
python3 - <<'PY'
from pathlib import Path
import json

path = Path.home() / ".agents" / "plugins" / "marketplace.json"
path.parent.mkdir(parents=True, exist_ok=True)

payload = {
    "name": "ai-kit",
    "interface": {
        "displayName": "ai-kit",
    },
    "plugins": [],
}

if path.exists():
    with path.open() as f:
        payload = json.load(f)

payload.setdefault("name", "ai-kit")
payload.setdefault("interface", {})
payload["interface"].setdefault("displayName", "ai-kit")
payload.setdefault("plugins", [])

entries = [
    {
        "name": "spec-workflow",
        "source": {
            "source": "local",
            "path": "./.codex/plugins/spec-workflow",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    },
    {
        "name": "tmux",
        "source": {
            "source": "local",
            "path": "./.codex/plugins/tmux",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Developer Tools",
    },
    {
        "name": "git",
        "source": {
            "source": "local",
            "path": "./.codex/plugins/git",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Coding",
    },
]

existing = []
seen = {entry["name"] for entry in entries}
for item in payload["plugins"]:
    if isinstance(item, dict) and item.get("name") not in seen:
        existing.append(item)

payload["plugins"] = existing + entries

with path.open("w") as f:
    json.dump(payload, f, indent=2)
    f.write("\n")

print(path)
PY
```

### 5. 安装 custom agents

```bash
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_agents.sh
```

### 6. 提示用户完成 Codex 内操作

执行完上面命令后，告诉用户：

1. 重启 Codex
2. 在插件目录里启用或安装：
   - `spec-workflow`
   - `tmux`
   - `git`

## 更新

更新时执行：

```bash
git -C ~/.codex/plugins/ai-kit-repo pull --ff-only
rm -rf ~/.codex/plugins/spec-workflow ~/.codex/plugins/tmux ~/.codex/plugins/git
cp -R ~/.codex/plugins/ai-kit-repo/plugins/spec-workflow ~/.codex/plugins/spec-workflow
cp -R ~/.codex/plugins/ai-kit-repo/plugins/tmux ~/.codex/plugins/tmux
cp -R ~/.codex/plugins/ai-kit-repo/plugins/git ~/.codex/plugins/git
cd ~/.codex/plugins/ai-kit-repo
bash scripts/install_codex_agents.sh
```

然后告诉用户：

1. 重启 Codex
2. 如果插件内容还是旧的，禁用并重新启用对应插件
3. 如果还不生效，卸载后重新安装对应插件

## 验证

执行：

```bash
test -f ~/.agents/plugins/marketplace.json
test -f ~/.codex/plugins/spec-workflow/.codex-plugin/plugin.json
test -f ~/.codex/plugins/tmux/.codex-plugin/plugin.json
test -f ~/.codex/plugins/git/.codex-plugin/plugin.json
test -f ~/.codex/agents/git-operator.toml
test -f ~/.codex/agents/tmux-operator.toml
```

安装完成后，插件命名空间应为：

- `spec-workflow:*`
- `tmux:*`
- `git:*`
