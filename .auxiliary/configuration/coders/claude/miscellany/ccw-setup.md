# Claude Code (Web) Session Setup

**Instructions for Claude instances**: Execute the following setup steps at the beginning of each Claude Code (Web) session to ensure all required tools are available.

## Required Setup Steps

### 1. Install System Packages

Install GitHub CLI from the latest release (ensures latest version instead of older Ubuntu package):

```bash
# Get latest version number and install
GH_VERSION=$(wget https://github.com/cli/cli/releases/latest -O - 2>&1 | grep -oP 'href="/cli/cli/releases/tag/v\K[0-9.]+' | head -1) && \
wget -O /tmp/gh_${GH_VERSION}_linux_amd64.deb https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.deb && \
dpkg -i /tmp/gh_${GH_VERSION}_linux_amd64.deb
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

### 6. Setup Bash Tool Bypass Wrapper

Copy the bash-tool-bypass script to PATH for accessing restricted commands:

```bash
cp .auxiliary/configuration/coders/claude/miscellany/bash-tool-bypass ~/.local/bin/
chmod +x ~/.local/bin/bash-tool-bypass
```

### 7. Verify Installation

Check that all required tools are available:

```bash
which mcp-language-server
which pyright
which ruff
which bash-tool-bypass
hatch --version
copier --version
agentsmgr --version
bash-tool-bypass gh --version
```

## Notes

- `librovore` MCP server does not require pre-installation; `uvx` will handle it automatically
- The `.mcp.json` configuration expects these tools to be in PATH
- Direct GitHub CLI installation avoids APT GPG signature verification issues
- The `bash-tool-bypass` wrapper enables execution of commands restricted by Claude Code Bash tool permissions
- `GH_TOKEN` environment variable should be configured in Claude Code settings for GitHub API authentication
