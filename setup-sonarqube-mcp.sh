#!/bin/bash

# SonarQube MCP Server Setup Script
# This script helps you configure the SonarQube MCP server for IronRoutine

set -e

echo "========================================="
echo "SonarQube MCP Server Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Pull the SonarQube MCP Docker image
echo "Pulling SonarQube MCP Server Docker image..."
if docker pull mcp/sonarqube; then
    echo -e "${GREEN}✓ Docker image pulled successfully${NC}"
else
    echo -e "${RED}Error: Failed to pull Docker image${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo "Configuration"
echo "========================================="
echo ""

# Prompt for SonarQube token
echo "Please enter your SonarQube token:"
echo "(You can generate one at: https://qube.shawncarter.co.uk/account/security)"
read -s SONARQUBE_TOKEN

if [ -z "$SONARQUBE_TOKEN" ]; then
    echo -e "${RED}Error: Token cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Token received${NC}"
echo ""

# Ask which MCP client to configure
echo "Which MCP client would you like to configure?"
echo "1) Claude Desktop"
echo "2) VS Code with GitHub Copilot"
echo "3) Cursor"
echo "4) Show manual configuration"
echo ""
read -p "Enter your choice (1-4): " CLIENT_CHOICE

case $CLIENT_CHOICE in
    1)
        CONFIG_FILE="$HOME/.claude.json"
        echo ""
        echo "Configuring Claude Desktop..."
        echo "Configuration file: $CONFIG_FILE"
        
        # Create backup if file exists
        if [ -f "$CONFIG_FILE" ]; then
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
            echo -e "${YELLOW}Backup created: $CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)${NC}"
        fi
        
        # Create configuration
        cat > "$CONFIG_FILE" << EOF
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
        "SONARQUBE_TOKEN": "$SONARQUBE_TOKEN",
        "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
      }
    }
  }
}
EOF
        echo -e "${GREEN}✓ Configuration created${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Restart Claude Desktop"
        echo "2. Test with: 'List my SonarQube projects'"
        ;;
        
    2)
        CONFIG_FILE=".vscode/mcp.json"
        echo ""
        echo "Configuring VS Code with GitHub Copilot..."
        echo "Configuration file: $CONFIG_FILE"
        
        # Create .vscode directory if it doesn't exist
        mkdir -p .vscode
        
        # Create backup if file exists
        if [ -f "$CONFIG_FILE" ]; then
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
            echo -e "${YELLOW}Backup created: $CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)${NC}"
        fi
        
        # Create configuration
        cat > "$CONFIG_FILE" << EOF
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
          "SONARQUBE_TOKEN": "$SONARQUBE_TOKEN",
          "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
        }
      }
    }
  }
}
EOF
        echo -e "${GREEN}✓ Configuration created${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Restart VS Code"
        echo "2. Open GitHub Copilot Chat"
        echo "3. Test with: 'List my SonarQube projects'"
        ;;
        
    3)
        CONFIG_FILE="$HOME/.cursor/mcp.json"
        echo ""
        echo "Configuring Cursor..."
        echo "Configuration file: $CONFIG_FILE"
        
        # Create .cursor directory if it doesn't exist
        mkdir -p "$HOME/.cursor"
        
        # Create backup if file exists
        if [ -f "$CONFIG_FILE" ]; then
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
            echo -e "${YELLOW}Backup created: $CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)${NC}"
        fi
        
        # Create configuration
        cat > "$CONFIG_FILE" << EOF
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
        "SONARQUBE_TOKEN": "$SONARQUBE_TOKEN",
        "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
      }
    }
  }
}
EOF
        echo -e "${GREEN}✓ Configuration created${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Restart Cursor"
        echo "2. Test with: 'List my SonarQube projects'"
        ;;
        
    4)
        echo ""
        echo "Manual Configuration:"
        echo "===================="
        echo ""
        echo "Add this to your MCP client configuration:"
        echo ""
        cat << EOF
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
        "SONARQUBE_TOKEN": "$SONARQUBE_TOKEN",
        "SONARQUBE_URL": "https://qube.shawncarter.co.uk"
      }
    }
  }
}
EOF
        echo ""
        echo "See sonarqube-mcp-setup.md for more details"
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "For more information, see: sonarqube-mcp-setup.md"

