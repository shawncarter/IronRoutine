# SonarQube MCP Server Integration

This directory contains configuration and setup files for integrating the SonarQube MCP (Model Context Protocol) server with your development environment.

## 📁 Files in This Setup

- **`SONARQUBE_MCP_QUICKSTART.md`** - Quick reference guide for common tasks
- **`sonarqube-mcp-setup.md`** - Detailed setup instructions for all MCP clients
- **`setup-sonarqube-mcp.sh`** - Automated setup script (recommended)
- **`.vscode/mcp.json.example`** - Example configuration for VS Code

## 🎯 What is SonarQube MCP Server?

The SonarQube MCP Server allows AI assistants (like Claude, GitHub Copilot, Cursor) to:
- Access your SonarQube code quality analysis
- Retrieve project metrics and issues
- Help you understand and fix code quality problems
- Provide security insights and recommendations

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./setup-sonarqube-mcp.sh
```

This script will:
1. ✅ Check Docker installation
2. ✅ Pull the SonarQube MCP Docker image
3. ✅ Prompt for your SonarQube token
4. ✅ Configure your preferred MCP client
5. ✅ Create backups of existing configurations

### Option 2: Manual Setup

1. **Get your SonarQube token**:
   - Visit: https://qube.shawncarter.co.uk/account/security
   - Generate a new token
   - Save it securely

2. **Pull the Docker image**:
   ```bash
   docker pull mcp/sonarqube
   ```

3. **Configure your MCP client**:
   - See `sonarqube-mcp-setup.md` for detailed instructions
   - Choose your client (Claude Desktop, VS Code, Cursor, etc.)
   - Update the configuration with your token

4. **Restart your MCP client**

## 🔧 Configuration

### Your SonarQube Server

- **URL**: `https://qube.shawncarter.co.uk`
- **Project Key**: `IronRoutine` (from `sonar-project.properties`)

### Required Environment Variables

- `SONARQUBE_TOKEN`: Your personal access token
- `SONARQUBE_URL`: Your SonarQube server URL

### Optional Environment Variables

- `LOG_FILE`: Path to log file for debugging
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARN, ERROR)

## 💬 Using the MCP Server

Once configured, you can ask your AI assistant:

### Project Information
```
"List all my SonarQube projects"
"Show me the metrics for IronRoutine"
"What's the code coverage for this project?"
```

### Issue Analysis
```
"Show me critical issues in IronRoutine"
"Find all bugs in workouts/views.py"
"List security vulnerabilities in the project"
"Show code smells that need attention"
```

### Quality Gates
```
"Check the quality gate status for IronRoutine"
"What are the quality gate conditions?"
"Did the last analysis pass the quality gate?"
```

### Security
```
"Find security hotspots in the project"
"Show me security vulnerabilities"
"Analyze security issues in the authentication module"
```

### Code Analysis
```
"Analyze the current file with SonarQube"
"Show me issues in this code snippet"
"What code quality issues exist in routines/views.py?"
```

## 🛠️ Supported MCP Clients

- **Claude Desktop** - Official Anthropic client
- **VS Code with GitHub Copilot** - Microsoft's AI assistant
- **Cursor** - AI-first code editor
- **Windsurf** - Available as a plugin
- **Gemini CLI** - Google's AI assistant
- **Zed** - Available as an extension

## 🔒 Security Notes

1. **Never commit your SonarQube token** to version control
2. The `.gitignore` file is configured to exclude MCP configuration files
3. Example files (`.example` suffix) are safe to commit
4. Tokens should have minimal required permissions

## 📊 Available Tools

The SonarQube MCP Server provides these tools:

- **projects** - List all projects
- **components** - Search and navigate code components
- **issues** - Search and filter issues
- **hotspots** - Find security hotspots
- **metrics** - Get available metrics
- **measures_component** - Get measures for a component
- **quality_gates** - List quality gates
- **quality_gate_status** - Check quality gate status
- **source_code** - View source code with issues
- **system_health** - Check SonarQube health

For a complete list, see: https://github.com/SonarSource/sonarqube-mcp-server

## 🐛 Troubleshooting

### Authentication Failed
- Verify your token is correct and not expired
- Check token permissions in SonarQube
- Generate a new token if needed

### Connection Refused
- Verify the SonarQube URL is accessible
- Check if the server is running
- Test the URL in your browser

### Docker Issues
- Ensure Docker is installed and running
- Try: `docker pull mcp/sonarqube`
- Check Docker logs for errors

### No Response from MCP Server
- Enable debug logging (see configuration)
- Check log file: `/tmp/sonarqube-mcp.log`
- Restart your MCP client

## 📚 Additional Resources

- **Official Documentation**: https://docs.sonarsource.com/sonarqube-for-vs-code/ai-capabilities/sonarqube-mcp-server
- **GitHub Repository**: https://github.com/SonarSource/sonarqube-mcp-server
- **MCP Protocol**: https://modelcontextprotocol.io/
- **SonarQube Documentation**: https://docs.sonarqube.org/

## 🔄 Updating

To update the SonarQube MCP Server:

```bash
docker pull mcp/sonarqube:latest
```

Then restart your MCP client.

## 💡 Tips

1. **Start Simple**: Begin with basic queries like "List my projects"
2. **Be Specific**: Reference specific files or components for better results
3. **Use Project Key**: Reference "IronRoutine" when asking about this project
4. **Enable Logging**: Helpful for debugging issues
5. **Check Permissions**: Ensure your token has access to the projects you need

## 🤝 Contributing

If you find issues or have suggestions for improving this setup:
1. Check the official documentation
2. Review the troubleshooting section
3. Enable debug logging to gather more information
4. Consult the SonarQube MCP Server GitHub repository

## 📝 License

The SonarQube MCP Server is provided by SonarSource.
See the official repository for license information.

---

**Last Updated**: 2025-01-14
**SonarQube Server**: qube.shawncarter.co.uk
**Project**: IronRoutine

