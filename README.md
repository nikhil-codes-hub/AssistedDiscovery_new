# AssistedDiscovery

A Streamlit-based application for XML pattern analysis and discovery using AI/LLM assistance.

## Features

- **Pattern Discovery**: Extract patterns from XML files using AI assistance
- **Pattern Verification**: Verify and validate extracted patterns
- **Pattern Management**: Save patterns to personal and shared workspaces
- **Multi-Workspace Support**: Organize patterns by different use cases/workspaces
- **Pattern Library**: Browse and filter all available patterns
- **Export/Import**: Export patterns and workspace data

## Setup Instructions

### Prerequisites

- Python 3.8+
- SQLite3

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create environment configuration:
   ```bash
   cp .env.example .env
   ```
5. Add your API keys to `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Application

```bash
streamlit run app/0_⚙️_Configuration.py
```

## Security

- API keys are automatically excluded from version control
- Database files are not committed to prevent data exposure
- Environment variables are used for sensitive configuration

⚠️ **Security Note**: Never commit API keys to version control.
EOF < /dev/null