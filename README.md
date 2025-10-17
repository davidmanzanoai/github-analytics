# GitHub Repository Analyzer Agent

@author: David Manzano Macho

An intelligent agent that analyzes GitHub repositories using Claude Sonnet 4 with MCP (Model Context Protocol) to answer questions about contributors, development velocity, code complexity, documentation, and more.

## Features

- 🔍 **Repository Analysis**: Deep insights into any GitHub repository
- 💬 **Conversational Interface**: Ask follow-up questions with context retention
- 📊 **Statistical Analysis**: Get concrete metrics on contributors, commits, and development patterns
- 🧠 **AI-Powered**: Uses Claude Sonnet 4 for intelligent code analysis
- 🔧 **MCP Integration**: Direct access to repository files, commits, and structure

## Prerequisites

- Python 3.8 or higher
- Node.js (for the MCP GitHub server)
- Anthropic API key

## Installation

1. **Clone or download this project**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Anthropic API key:**
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```
   
   Or create a `.env` file:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

4. **Verify Node.js is installed:**
   ```bash
   node --version
   ```
   
   The MCP GitHub server (`@modelcontextprotocol/server-github`) will be automatically installed via npx when the agent runs.

## Usage

### Basic Usage

```python
from github_agent import GitHubRepoAgent

# Initialize the agent
agente = GitHubRepoAgent()

# Ask a quick question
respuesta = agente.pregunta_rapida(
    "facebook", 
    "react",
    "Who is the main contributor? Give me concrete statistics."
)
print(respuesta)
```

### Conversational Analysis

```python
# Initialize agent
agente = GitHubRepoAgent()

# Start analysis
resp1 = agente.analizar_repo(
    "facebook",
    "react",
    "Give me a general summary of the repository"
)
print(resp1)

# Continue the conversation with context
resp2 = agente.conversacion_continua(
    "What are the main programming languages used?"
)
print(resp2)
```

### Run the Example

```bash
python github_agent.py
```

Edit the `OWNER` and `REPO` variables in the `__main__` section to analyze any repository.

## Example Questions

Here are some example questions you can ask the agent:

- "Who is the main contributor and how many commits do they have?"
- "Analyze the development velocity in the last 3 months"
- "What is the most complex module in the codebase?"
- "Review the quality of the documentation"
- "What technologies and frameworks are used?"
- "Look for potential security issues"
- "What are the most recently modified files?"
- "Analyze the testing coverage and test structure"
- "What are the main dependencies of this project?"

## How It Works

The agent uses Claude Sonnet 4 with MCP (Model Context Protocol), which allows it to:

1. **Access repository structure**: List files and directories
2. **Read file contents**: Examine source code, documentation, and configuration files
3. **Analyze commits**: Review commit history and contribution patterns
4. **Search patterns**: Find specific code patterns and implementations

The MCP integration provides direct access to the GitHub repository, enabling Claude to give precise, data-backed answers based on actual repository contents.

## API Methods

### `GitHubRepoAgent(api_key=None)`
Initialize the agent. If `api_key` is not provided, it will use the `ANTHROPIC_API_KEY` environment variable.

### `analizar_repo(owner, repo, pregunta)`
Analyze a repository and answer a specific question. Maintains conversation history.

**Parameters:**
- `owner` (str): Repository owner (e.g., "facebook")
- `repo` (str): Repository name (e.g., "react")
- `pregunta` (str): Question to answer

**Returns:** String with the analysis result

### `pregunta_rapida(owner, repo, pregunta)`
Ask a quick question without maintaining conversation context.

**Parameters:**
- `owner` (str): Repository owner
- `repo` (str): Repository name
- `pregunta` (str): Question to answer

**Returns:** String with the answer

### `conversacion_continua(pregunta)`
Continue a conversation about the same repository with maintained context.

**Parameters:**
- `pregunta` (str): Follow-up question

**Returns:** String with the answer

## License

MIT

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
