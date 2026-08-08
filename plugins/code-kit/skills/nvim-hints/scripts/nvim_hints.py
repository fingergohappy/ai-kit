#!/usr/bin/env python3
"""Apply or clear code-path hints (quickfix list + virtual text) in a running Neovim.

Usage:
    nvim_hints.py check <socket>              # verify the socket is reachable
    nvim_hints.py apply <socket> <hints.json> # clear old hints, then apply new ones
    nvim_hints.py clear <socket>              # remove all hints and empty the qflist

hints.json schema:
{
  "title": "qflist title shown in the quickfix window",
  "items": [
    {
      "file": "/absolute/path/to/file.go",
      "line": 42,
      "col": 1,                # optional, defaults to 1
      "text": "1. Foo() — entry point",   # shown in the quickfix list
      "hint": "short note"     # optional virtual text; falls back to "text"
    }
  ]
}
"""
import json
import os
import subprocess
import sys
import tempfile

LUA_APPLY = r"""
local payload = vim.json.decode([==[
@PAYLOAD@
]==])
local ns = vim.api.nvim_create_namespace("claude_hints")
for _, buf in ipairs(vim.api.nvim_list_bufs()) do
  if vim.api.nvim_buf_is_loaded(buf) then
    vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)
  end
end
if payload.action == "clear" then
  vim.fn.setqflist({}, " ", { title = "claude-hints (cleared)", items = {} })
  pcall(vim.cmd, "cclose")
  return "cleared"
end
vim.api.nvim_set_hl(0, "ClaudeHint", { link = "DiagnosticVirtualTextInfo", default = true })
local qf = {}
local problems = {}
for _, item in ipairs(payload.items) do
  if not (vim.uv or vim.loop).fs_stat(item.file) then
    table.insert(problems, "missing: " .. item.file)
  else
    local buf = vim.fn.bufadd(item.file)
    vim.fn.bufload(buf)
    vim.bo[buf].buflisted = true
    local lcount = vim.api.nvim_buf_line_count(buf)
    local lnum = math.min(item.line, lcount)
    if lnum ~= item.line then
      table.insert(problems, string.format("line clamped %s:%d->%d", item.file, item.line, lnum))
    end
    local hint = item.hint or item.text
    pcall(vim.api.nvim_buf_set_extmark, buf, ns, lnum - 1, 0, {
      virt_text = { { "  ⟸ " .. hint, "ClaudeHint" } },
      virt_text_pos = "eol",
      hl_mode = "combine",
    })
    table.insert(qf, { bufnr = buf, lnum = lnum, col = item.col or 1, text = item.text })
  end
end
vim.fn.setqflist({}, " ", { title = payload.title or "claude-hints", items = qf })
if #qf > 0 then
  vim.cmd("copen | wincmd p")
end
local msg = string.format("applied %d hints", #qf)
if #problems > 0 then
  msg = msg .. " | " .. table.concat(problems, "; ")
end
return msg
"""


def remote_lua(socket: str, lua_src: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".lua", prefix="nvim_hints_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(lua_src)
        expr = "luaeval('dofile(_A)', '%s')" % path
        proc = subprocess.run(
            ["nvim", "--server", socket, "--remote-expr", expr],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            raise SystemExit("nvim remote call failed: %s" % (proc.stderr.strip() or proc.stdout.strip()))
        return proc.stdout.strip()
    finally:
        os.unlink(path)


def build_lua(payload: dict) -> str:
    blob = json.dumps(payload, ensure_ascii=False)
    if "]==]" in blob:
        raise SystemExit("payload contains ']==]', refusing to embed")
    return LUA_APPLY.replace("@PAYLOAD@", blob)


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    cmd, socket = sys.argv[1], sys.argv[2]
    if cmd == "check":
        proc = subprocess.run(
            ["nvim", "--server", socket, "--remote-expr", "join([bufname('%'), getcwd()], ' | ')"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode != 0:
            raise SystemExit("unreachable: %s" % (proc.stderr.strip() or proc.stdout.strip()))
        print("ok: %s" % proc.stdout.strip())
    elif cmd == "apply":
        if len(sys.argv) < 4:
            raise SystemExit("apply requires a hints.json path")
        with open(sys.argv[3]) as f:
            payload = json.load(f)
        if not payload.get("items"):
            raise SystemExit("hints.json has no items")
        print(remote_lua(socket, build_lua(payload)))
    elif cmd == "clear":
        print(remote_lua(socket, build_lua({"action": "clear"})))
    else:
        raise SystemExit("unknown command: %s\n%s" % (cmd, __doc__))


if __name__ == "__main__":
    main()
