# SonarQube MCP Quick Start

## 🚀 Quick Setup (Recommended)

Run the automated setup script:

```bash
./setup-sonarqube-mcp.sh
```

This will:
1. Check Docker installation
2. Pull the SonarQube MCP Docker image
3. Prompt for your SonarQube token
4. Configure your preferred MCP client

## 📋 Manual Setup

### Step 1: Get Your SonarQube Token

1. Go to: https://qube.shawncarter.co.uk/account/security
2. Click "Generate Token"
3. Give it a name (e.g., "MCP Server")
4. Copy the token (you won't see it again!)

### Step 2: Pull Docker Image

```bash
docker pull mcp/sonarqube
```

### Step 3: Configure Your MCP Client

Choose your client and follow the configuration in `sonarqube-mcp-setup.md`

## 🧪 Test Your Setup

Once configured, test with your AI assistant:

```
"List my SonarQube projects"
"Show me issues in the IronRoutine project"
"What's the code quality for IronRoutine?"
```

## 🛠️ Available Commands

### Project Analysis
- "List all my SonarQube projects"
- "Show project metrics for IronRoutine"
- "What's the code coverage for IronRoutine?"

### Issue Management
- "Show me critical issues in IronRoutine"
- "Find all bugs in the project"
- "List security vulnerabilities"
- "Show code smells in workouts/views.py"

### Quality Gates
- "Check quality gate status for IronRoutine"
- "Show quality gate conditions"

### Security
- "Find security hotspots in IronRoutine"
- "Show security vulnerabilities"

## 🔧 Troubleshooting

### "Authentication failed"
- Check your token is correct
- Verify token hasn't expired
- Generate a new token if needed

### "Connection refused"
- Verify URL: https://qube.shawncarter.co.uk
- Check if SonarQube server is accessible
- Test in browser first

### "Docker not found"
- Install Docker: https://docs.docker.com/get-docker/
- Make sure Docker is running

## 📚 More Information

- Full setup guide: `sonarqube-mcp-setup.md`
- Official docs: https://docs.sonarsource.com/sonarqube-for-vs-code/ai-capabilities/sonarqube-mcp-server
- GitHub repo: https://github.com/SonarSource/sonarqube-mcp-server

## 🎯 Project Configuration

Your project is already configured with:
- Project Key: `IronRoutine` (from sonar-project.properties)
- Server URL: `https://qube.shawncarter.co.uk`

## 💡 Pro Tips

1. **Enable Debug Logging**: Add to your config:
   ```json
   "LOG_FILE": "/tmp/sonarqube-mcp.log",
   "LOG_LEVEL": "DEBUG"
   ```

2. **Check Logs**: If issues occur, check the log file for details

3. **Token Permissions**: Make sure your token has at least "Browse" permission

4. **Multiple Projects**: The MCP server can access all projects you have permissions for

