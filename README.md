# AI Research Assistant

An intelligent research assistant that generates detailed reports on any topic using PydanticAI, Tavily for search, and FireCrawl for web content extraction.

## Features

- **Intelligent Search**: Uses Tavily's advanced search API to find relevant and reliable sources
- **Smart Content Extraction**: Utilizes FireCrawl to extract clean, formatted content from web pages
- **Advanced Content Processing**:
  - Intelligent content chunking for handling large documents
  - Token-aware processing to prevent context window limits
  - Smart paragraph and sentence splitting
  - Efficient memory usage
- **Structured Reports**:
  - Clear, engaging titles
  - Comprehensive introductions
  - Well-organized body sections
  - Meaningful conclusions
  - Properly cited sources with hyperlinks
- **Quality Control**:
  - Validates all sources and citations
  - Ensures comprehensive coverage
  - Maintains consistent structure
  - Token-aware content processing
- **User Interface**:
  - Modern Streamlit web interface
  - Clean and intuitive design
  - Real-time progress updates
  - Raw markdown preview option
  - One-click report downloads
- **Flexible Output**:
  - Markdown formatting for readability
  - Rich console output with progress indicators
  - Automatic file saving with timestamps
- **Error Handling**:
  - Graceful handling of unsupported websites
  - Smart URL validation with multiple format support
  - Fallback content extraction methods
  - Token limit management

## Setup

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment variables:

   Copy the example.env file to create your own .env file:

   ```bash
   cp example.env .env
   ```

   Then edit the `.env` file with your API keys:

   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   # Optional for alternative models
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

   - Get your OpenAI API key from [OpenAI](https://platform.openai.com/api-keys)
   - Get your Tavily API key from [Tavily](https://tavily.com)
   - Get your FireCrawl API key from [FireCrawl](https://firecrawl.co)
   - (Optional) Get your OpenRouter API key from [OpenRouter](https://openrouter.ai)

3. Version Control:

   The project includes a `.gitignore` file that excludes:

   - Environment files (.env)
   - Generated reports (reports/, research*report*\*.md)
   - Python cache files (**pycache**/)
   - Virtual environments (venv/, .env/)
   - IDE settings (.vscode/, .idea/)
   - Log files (.logfire/, \*.log)
   - System files (.DS_Store)

   Make sure to never commit sensitive information like API keys to version control.

## Usage

### Web Interface (Recommended)

Run the Streamlit web interface:

```bash
streamlit run streamlit_app.py
```

This will open a browser window with the research assistant interface where you can:

1. Enter your research topic
2. Click "Generate Report" to start the research
3. View the report with real-time progress updates
4. Toggle between rendered and raw markdown views
5. Download the report as a markdown file

### Command Line Interface

Alternatively, you can use the command-line interface:

```bash
python research_assistant.py
```

## Configuration Options

### Language Models

The assistant supports multiple language models:

- Default: `openai:gpt-4o-mini`
- Alternative models through OpenRouter (uncomment and modify in code):
  ```python
  model = OpenAIModel(
      'deepseek/deepseek-chat',
      base_url='https://openrouter.ai/api/v1',
      api_key=openrouter_api_key,
  )
  ```

### Search Configuration

Tavily search can be configured with:

- `search_depth`: "advanced" for comprehensive results
- `include_raw_content`: True to get full content
- Additional parameters available in Tavily documentation

### Content Processing

The assistant includes advanced content processing features:

- **Token Management**:

  - Automatically counts and manages tokens using tiktoken
  - Prevents context window overflow
  - Configurable chunk sizes (default: 8000 tokens)

- **Content Chunking**:
  - Smart paragraph-based splitting
  - Sentence-level chunking for large paragraphs
  - Context-aware content processing
  - Memory-efficient operation

### Content Extraction

FireCrawl extraction supports:

- Markdown format for structured content
- Fallback to plain text when needed
- Automatic handling of unsupported websites

## Output Format

The generated report includes:

```markdown
# Title

_Generated on YYYY-MM-DD HH:MM:SS_

## Introduction

[Introduction content with hyperlinks]

## [Body Section 1]

[Section content with hyperlinks]

## [Body Section 2]

[Section content with hyperlinks]

## Conclusion

[Conclusion content with hyperlinks]

## Sources

1. [Source Title](URL)
   > Relevant quote or summary
```

## Error Handling

The assistant includes robust error handling for:

- Unsupported websites
- Invalid URLs
- Failed content extraction
- Network issues
- API rate limits
- Token limit exceeded scenarios
- Memory constraints

Errors are displayed with color-coded messages in both the web interface and console:

- Red: Critical errors
- Yellow: Warnings
- Cyan: Progress updates
- Green: Success messages
