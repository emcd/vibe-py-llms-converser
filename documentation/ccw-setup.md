# Claude Code (Web) Session Setup

**Instructions for Claude instances**: Execute the following setup steps at the beginning of each Claude Code (Web) session to ensure all required tools are available.

## Required Setup Steps

### 1. Install System Packages

```bash
apt update && apt install -y gh
```

### 2. Install Core Python Tools

```bash
uv tool install hatch
uv tool install copier
uv tool install emcd-agents
```

### 3. Populate Project Agents

```bash
agentsmgr populate project github:emcd/agents-common@master#defaults
```

### 4. Configure Environment

Set up Go paths for persistent access. Append to `~/.local/bin/env`:

```bash
cat >> ~/.local/bin/env << 'EOF'

# Add Go bin to PATH
export GOPATH="${HOME}/.local/share/go"
case ":${PATH}:" in
    *:"${GOPATH}/bin":*)
        ;;
    *)
        export PATH="${GOPATH}/bin:${PATH}"
        ;;
esac
EOF
```

Source the updated environment:

```bash
source ~/.local/bin/env
```

### 5. Install Language Servers

Install `mcp-language-server` (proxies language servers for MCP):

```bash
go install github.com/isaacphi/mcp-language-server@latest
```

Install Pyright (Python language server):

```bash
npm install -g pyright
```

Install Ruff (Python linter/formatter):

```bash
uv tool install ruff
```

### 6. Verify Installation

Check that all required tools are available:

```bash
which mcp-language-server
which pyright
which ruff
hatch --version
copier --version
agentsmgr --version
```

## Notes

- `librovore` MCP server does not require pre-installation; `uvx` will handle it automatically
- The `.mcp.json` configuration expects these tools to be in PATH
