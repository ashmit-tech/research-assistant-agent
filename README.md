# PyAI Research Assistant Agent

A powerful research assistant that generates detailed reports on any topic using PydanticAI and Tavily's search API. The assistant uses advanced AI to create well-structured, properly cited research reports with real-time progress updates.

## Features

### Search and Research

- Advanced semantic search using Tavily API
- Intelligent source validation and citation
- Real-time search result processing
- Automatic content summarization

### Report Generation

- Well-structured research reports with proper citations
- Smart section organization based on available sources
- Automatic source validation and verification
- Hyperlinked citations and references

### User Interface

- Modern Streamlit web interface
- Clean and intuitive design
- Real-time progress updates
- Raw markdown preview option
- One-click report downloads

### Output Management

- Markdown-formatted reports
- Automatic report saving with timestamps
- Organized report storage in dedicated directory
- Rich console output with progress indicators

### Error Handling

- Graceful error recovery
- Clear error messages and warnings
- Smart retry mechanism for failed requests
- Comprehensive error logging

## Installation

### Prerequisites

- Python 3.9+
- Git
- Conda (Recommended)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/ashmit-tech/research-assistant-agent.git
cd pyai-research-assistant-agent
```

2. Create and activate a conda environment:

```bash
conda create -n research-assistant python=3.9
conda activate research-assistant
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:

```bash
cp example.env .env
```

5. Add your API keys to the `.env` file:

```
TAVILY_API_KEY=your_tavily_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Usage

### Command Line Interface

Run the research assistant from the command line:

```bash
python research_assistant.py
```

### Web Interface

Run the Streamlit web interface:

```bash
streamlit run streamlit_app.py
```

## Output Structure

The research assistant generates well-structured reports in markdown format:

```markdown
# Research Title

_Generated on YYYY-MM-DD HH:MM:SS_

## Introduction

[Introduction content with context and scope]
[Citations and hyperlinks to sources]

## [Body Section 1]

[Section content with detailed analysis]
[Citations and hyperlinks to sources]

## [Body Section 2]

[Section content with detailed analysis]
[Citations and hyperlinks to sources]

## Conclusion

[Summary and key findings]
[Citations and hyperlinks to sources]

## Sources

1. [Source Title](URL)

   > Relevant quote or summary from the source

2. [Source Title](URL)
   > Relevant quote or summary from the source
```

### Report Features

- Clear section organization
- Proper citation formatting
- Hyperlinked references
- Source summaries and quotes
- Automatic timestamp
- Consistent markdown styling

Reports are automatically saved in the `reports` directory with timestamps in the format: `research_report_YYYYMMDD_HHMMSS.md`

## API Keys

- Get your Tavily API key from: [https://tavily.com](https://tavily.com)
- Get your OpenRouter API key from: [https://openrouter.ai](https://openrouter.ai)

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT License - see LICENSE file for details.
