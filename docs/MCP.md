# Model Context Protocol (MCP) Configuration

## Overview
This repository includes MCP configuration files for AI assistants that support the Model Context Protocol. MCP allows AI assistants to securely interact with external tools and data sources.

## Configuration Files

### Repository Root: `mcp.json`
The main MCP configuration file at the repository root contains safe default servers:

```json
{
  "mcpServers": {
    "fs": {
      "command": "fs",
      "args": []
    }
  }
}
```

This includes only the basic filesystem server for safe file operations.

### VS Code: `.vscode/mcp.json`  
The VS Code specific MCP configuration mirrors the root configuration:

```json
{
  "mcpServers": {
    "fs": {
      "command": "fs",
      "args": []
    }
  }
}
```

## Adding MCP Servers

To add additional MCP servers for enhanced functionality:

### 1. Database Servers
```json
{
  "mcpServers": {
    "fs": {
      "command": "fs", 
      "args": []
    },
    "sqlite": {
      "command": "sqlite",
      "args": ["data/agent_unified.db"]
    }
  }
}
```

### 2. Web Search Servers
```json
{
  "mcpServers": {
    "fs": {
      "command": "fs",
      "args": []
    },
    "web-search": {
      "command": "web-search",
      "args": [],
      "env": {
        "SEARCH_API_KEY": "your-search-api-key"
      }
    }
  }
}
```

### 3. Git Servers
```json
{
  "mcpServers": {
    "fs": {
      "command": "fs",
      "args": []
    },
    "git": {
      "command": "git",
      "args": ["."]
    }
  }
}
```

## Security Guidelines

### [WARN] Important Security Notes
- **Never commit API keys or secrets** in MCP configuration files
- Use environment variables for sensitive configuration
- Test MCP servers in development before production use
- Keep MCP configurations minimal and only add needed servers

### Environment Variables
For servers requiring authentication, use environment variables:

```json
{
  "mcpServers": {
    "api-server": {
      "command": "api-server",
      "args": [],
      "env": {
        "API_KEY": "${API_KEY}",
        "API_SECRET": "${API_SECRET}"
      }
    }
  }
}
```

Then set these in your `.env` file (which is already in `.gitignore`):
```bash
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
```

## VS Code Integration

If using VS Code with MCP support:

1. The `.vscode/mcp.json` file will be automatically detected
2. MCP servers will be available in the VS Code AI assistant
3. Update both `mcp.json` and `.vscode/mcp.json` to keep them synchronized

## Available MCP Servers

Common MCP servers you might want to add:
- `fs` - Filesystem operations (included by default)
- `sqlite` - SQLite database access
- `git` - Git repository operations  
- `web-search` - Web search capabilities
- `calendar` - Calendar integration
- `email` - Email operations
- `slack` - Slack integration

## Configuration Management

### Adding New Servers
1. Update `mcp.json` at repository root
2. Update `.vscode/mcp.json` to match
3. Test the new server configuration
4. Document any environment variables needed

### Removing Servers
1. Remove from both configuration files
2. Clean up any associated environment variables
3. Update documentation

## Troubleshooting

### Common Issues
- **Server not found**: Ensure the MCP server binary is installed and in PATH
- **Authentication failures**: Check environment variables are set correctly
- **Permission denied**: Verify file/directory permissions for server access

### Testing Configuration
```bash
# Test MCP configuration
cat mcp.json | jq .

# Validate JSON syntax
python -c "import json; json.load(open('mcp.json'))"
```

## Best Practices

1. **Start minimal**: Begin with just the `fs` server
2. **Add incrementally**: Add one server at a time and test
3. **Use environment variables**: Never hardcode secrets
4. **Keep synchronized**: Update both `mcp.json` and `.vscode/mcp.json`
5. **Document changes**: Update this README when adding servers
6. **Test thoroughly**: Verify new servers work before committing

---

**Note**: MCP configuration files contain no secrets by default. All sensitive data should be provided via environment variables defined in `.env` (which is excluded from git via `.gitignore`).