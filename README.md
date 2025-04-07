# Self-Reflection Claude

![Self-Reflection Claude Demo](https://github.com/user-attachments/assets/f99cda6f-f804-4fe7-9182-520e80855b9f)

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

## 🛠️ Technical Implementation

Self-Reflection Claude consists of:

1. **MCP Server**: Provides tools and resources for autonomous learning
2. **SQLite Database**: Stores learning scenarios, conversation state, and searchable terms
3. **Client Application**: For testing and managing the learning database
4. **Claude Desktop Integration**: For seamless integration with Claude

## 📊 How It Works

### Learning Process:

1. **User Interaction**: User asks a question that Claude might get wrong
2. **Error Detection**: Claude detects an error (either self-detected or user-corrected)
3. **Automatic Correction**: Claude provides the correct answer with an explanation
4. **Background Learning**: The system automatically records the scenario for future reference
5. **Knowledge Application**: In future conversations, Claude recalls past learnings when faced with similar queries

## 💻 Installation

### Prerequisites:
- Python 3.10 or higher
- Claude Desktop application
- Basic understanding of the command line

### Steps:

1. Clone this repository:
```bash
git clone https://github.com/yourusername/self-reflection-claude.git
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

## 🧠 Technical Design

### Database Schema:

- **scenarios**: Stores learning events (questions, incorrect answers, corrections)
- **conversations**: Tracks ongoing conversation state
- **keyterms**: Indexes important terms for efficient searching

### Key Components:

- **Context Retrieval**: `get_conversation_context()` provides relevant past learnings
- **Error Recording**: `detect_and_record_correction()` captures learning events
- **Knowledge Recall**: `recall_relevant_knowledge()` retrieves applicable learnings

## 🔜 Future Improvements

- Add embedding-based similarity for better scenario matching
- Implement more sophisticated NLP for keyterm extraction
- Add privacy controls and data retention policies
- Support for multi-modal learning scenarios
- Cloud synchronization of learning database

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
