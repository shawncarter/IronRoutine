# SonarQube MCP Server Setup Guide

This guide will help you configure the SonarQube MCP (Model Context Protocol) server to connect to your SonarQube instance at `qube.shawncarter.co.uk`.

## Prerequisites

1. **SonarQube Token**: You need a user token from your SonarQube server
   - Go to `https://qube.shawncarter.co.uk/account/security`
   - Generate a new token with appropriate permissions
   - Save this token securely

2. **Docker**: Required for running the MCP server
   - Make sure Docker is installed and running

3. **MCP Client**: Choose one of the supported clients:
   - Claude Desktop (recommended)
   - VS Code with GitHub Copilot
   - Cursor
   - Windsurf

## Configuration Files

### For Claude Desktop

Create or edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "sonarqube": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "SONARQUBE_TOKEN",
        "-e",
        "SONARQUBE_URL",
        "mcp/sonarqube"
      ],
      "env": {
        "SONARQUBE_TOKEN": "YOUR_SONARQUBE_TOKEN_HERE",
        "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
      }
    }
  }
}
```

### For VS Code with GitHub Copilot

Create `.vscode/mcp.json` in your project:

```json
{
  "mcp": {
    "servers": {
      "sonarqube": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "SONARQUBE_TOKEN",
          "-e",
          "SONARQUBE_URL",
          "mcp/sonarqube"
        ],
        "env": {
          "SONARQUBE_TOKEN": "YOUR_SONARQUBE_TOKEN_HERE",
          "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
        }
      }
    }
  }
}
```

### For Cursor

Create `mcp.json` in your Cursor configuration directory:

```json
{
  "mcpServers": {
    "sonarqube": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "SONARQUBE_TOKEN",
        "-e",
        "SONARQUBE_URL",
        "mcp/sonarqube"
      ],
      "env": {
        "SONARQUBE_TOKEN": "YOUR_SONARQUBE_TOKEN_HERE",
        "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
      }
    }
  }
}
```

## Environment Variables

Replace `YOUR_SONARQUBE_TOKEN_HERE` with your actual SonarQube token.

Required variables:
- `SONARQUBE_TOKEN`: Your SonarQube user token
- `SONARQUBE_URL`: Your SonarQube server URL (https://qube.shawncarter.co.uk)

Optional variables:
- `LOG_FILE`: Path to log file for debugging (e.g., `/tmp/sonarqube-mcp.log`)
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARN, ERROR)

## Testing the Setup

1. **Pull the Docker image**:
   ```bash
   docker pull mcp/sonarqube
   ```

2. **Test connection manually**:
   ```bash
   docker run -i --rm \
     -e SONARQUBE_TOKEN="your_token_here" \
     -e SONARQUBE_URL="https://qube.shawncarter.co.uk" \
     mcp/sonarqube
   ```

3. **Restart your MCP client** (Claude Desktop, VS Code, etc.)

## Available Tools

Once configured, you can use these SonarQube tools in your AI assistant:

- **Project Analysis**: "List all my SonarQube projects"
- **Issue Investigation**: "Show me critical issues in IronRoutine project"
- **Code Quality**: "What's the code coverage for IronRoutine?"
- **Security**: "Find security hotspots in my project"
- **Quality Gates**: "Check quality gate status for IronRoutine"

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   - Verify your token is correct and not expired
   - Check token permissions in SonarQube

2. **Connection Refused**:
   - Verify the SonarQube URL is correct
   - Check if the server is accessible

3. **Docker Issues**:
   - Ensure Docker is running
   - Try pulling the image manually: `docker pull mcp/sonarqube`

### Debug Mode

Enable logging for troubleshooting:

```json
{
  "env": {
    "SONARQUBE_TOKEN": "your_token",
    "SONARQUBE_URL": "https://qube.shawncarter.co.uk",
    "LOG_FILE": "/tmp/sonarqube-mcp.log",
    "LOG_LEVEL": "DEBUG"
  }
}
```

## Next Steps

1. Generate your SonarQube token
2. Choose your preferred MCP client configuration
3. Update the configuration file with your token
4. Restart your MCP client
5. Test with: "List my SonarQube projects"

For more advanced configuration options, see the official documentation at:
https://docs.sonarsource.com/sonarqube-for-vs-code/ai-capabilities/sonarqube-mcp-server
