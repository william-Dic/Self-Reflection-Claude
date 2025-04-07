# Self-Reflection Claude

https://github.com/user-attachments/assets/f99cda6f-f804-4fe7-9182-520e80855b9f

## 🚀 Overview

**Self-Reflection Claude** is an autonomous learning system for Claude that enables it to:
- Automatically detect and correct errors without explicit prompting
- Record learned corrections in a structured database
- Recall past learnings when encountering similar questions
- Continuously improve through natural interactions

Built using the [Model Context Protocol (MCP)](https://www.anthropic.com/news/model-context-protocol), this system creates a self-improving feedback loop that makes Claude's responses more accurate and consistent over time.

## ✨ Features

- **Autonomous Error Detection**: Claude recognizes when it makes a mistake, either from user feedback or self-reflection
- **Automatic Knowledge Capture**: Errors and corrections are stored without requiring explicit commands
- **Structured Learning Database**: SQLite database with tables for scenarios, conversations, and searchable terms
- **Semantic Similarity Search**: Find similar scenarios based on query similarity and keyword matching
- **Conversation State Management**: Track ongoing conversations to enable contextual learning
- **Testing and Simulation Tools**: Dedicated client for testing the system without Claude Desktop

## 💻 Installation

### Steps:

1. Clone this repository:
```bash
git clone https://github.com/william-Dic/Self-Reflection-Claude.git
cd self-reflection-claude
```

2. Create a virtual environment:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install "mcp[cli]" httpx
```

4. Configure Claude Desktop:
Edit the Claude Desktop configuration file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this configuration (replace paths with your actual paths):
```json
{
  "mcpServers": {
    "self-reflection-claude": {
      "command": "PATH_TO_YOUR_VENV\\Scripts\\python.exe",
      "args": [
        "PATH_TO_YOUR_PROJECT\\autonomous_self_reflection.py"
      ]
    }
  }
}
```

5. Restart Claude Desktop and start using Self-Reflection Claude!

## 🧪 Testing with the CLI Client

To test the system without Claude Desktop:

```bash
python autonomous_client.py autonomous_self_reflection.py
```

This opens an interactive CLI that allows you to:
- Simulate conversations with error detection
- Check for similar scenarios
- View recent learnings
- Test knowledge recall
- Clear the learning database

## 🔜 Future Improvements

- Add embedding-based similarity for better scenario matching
- Implement more sophisticated NLP for keyterm extraction
- Add privacy controls and data retention policies
- Support for multi-modal learning scenarios
- Cloud synchronization of learning database

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
