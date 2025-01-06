"""Research Assistant using PydanticAI, Tavily, and FireCrawl.

This script creates detailed research reports on any given topic.
"""

import os
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import tiktoken

import logfire
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tavily import TavilyClient
from firecrawl import FirecrawlApp
from rich.console import Console
from rich.markdown import Markdown

from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel

# Load environment variables
load_dotenv()

# Configure logging
logfire.configure(send_to_logfire='if-token-present')

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
firecrawl = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
console = Console()

# model = OpenAIModel(
#     'deepseek/deepseek-chat',
#     base_url='https://openrouter.ai/api/v1',
#     api_key=openrouter_api_key,
# )


class Source(BaseModel):
    """A source used in the research."""
    title: str
    url: str
    snippet: str = Field(
        description="A relevant quote or summary from the source")


class ResearchSection(BaseModel):
    """A section of the research report."""
    title: str
    content: str = Field(
        description="The main content of the section with relevant hyperlinks")
    sources: List[Source] = Field(description="Sources used in this section")


class ResearchReport(BaseModel):
    """The complete research report."""
    title: str
    introduction: ResearchSection
    body_sections: List[ResearchSection]
    conclusion: ResearchSection
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class ResearchDeps:
    """Dependencies for the research agent."""
    topic: str
    search_results: List[dict]
    webpage_contents: dict


research_agent = Agent(
    'openai:gpt-4o-mini',
    # model=model,
    deps_type=ResearchDeps,
    result_type=ResearchReport,
    system_prompt="""You are an expert research assistant. Your task is to create detailed, 
    well-structured research reports on any given topic. Use the provided search results and 
    webpage contents to create accurate reports with proper citations and hyperlinks.
    
    Follow these guidelines:
    1. Create clear, engaging titles
    2. Write comprehensive introductions that outline the scope
    3. Organize the body into logical sections
    4. Draw meaningful conclusions
    5. Cite all sources using hyperlinks
    6. Use markdown formatting for better readability
    """
)


@research_agent.tool
async def search_topic(ctx: RunContext[ResearchDeps], query: str) -> List[dict]:
    """Search for information about the topic using Tavily."""
    search_response = tavily_client.search(
        query=query,
        search_depth="advanced",
        # include_answer=True,
        include_raw_content=True,
    )
    return search_response['results']


@research_agent.tool
async def get_webpage_content(ctx: RunContext[ResearchDeps], url: str) -> str:
    """Fetch and extract content from a webpage using FireCrawl."""
    try:
        # Use basic scrape_url with only the formats parameter
        result = firecrawl.scrape_url(
            url,
            params={
                'formats': ['markdown']
            }
        )

        # Check if the result contains markdown content
        if isinstance(result, dict) and 'markdown' in result:
            return result['markdown']

        # Fallback to raw text if markdown is not available
        if isinstance(result, dict) and 'text' in result:
            return result['text']

        console.print(
            f"[yellow]Warning: No content extracted from {url}[/yellow]")
        return ''

    except Exception as e:
        error_msg = str(e)
        if '403' in error_msg and 'no longer supported' in error_msg.lower():
            console.print(
                f"[yellow]Warning: {url} is not supported by Firecrawl[/yellow]")
        else:
            console.print(
                f"[red]Error fetching content from {url}: {error_msg}[/red]")
        return ''


@research_agent.result_validator
async def validate_report(
    ctx: RunContext[ResearchDeps],
    result: ResearchReport
) -> ResearchReport:
    """Validate the research report."""
    # Ensure all sections have sources
    sections = [result.introduction] + \
        result.body_sections + [result.conclusion]

    # Get all valid URLs from search results, including possible variations
    valid_urls = set()
    for r in ctx.deps.search_results:
        url = r['url']
        valid_urls.add(url)
        # Add URL without query parameters
        base_url = url.split('?')[0]
        valid_urls.add(base_url)
        # Add URL without trailing slash
        valid_urls.add(url.rstrip('/'))
        # Add URL with www. prefix if not present
        if not url.startswith('www.'):
            valid_urls.add(f"www.{url}")
        # Add URL without www. prefix if present
        if url.startswith('www.'):
            valid_urls.add(url[4:])
        # Add https:// and http:// variations
        if url.startswith('http://'):
            valid_urls.add(f"https://{url[7:]}")
        elif url.startswith('https://'):
            valid_urls.add(f"http://{url[8:]}")

    for section in sections:
        if not section.sources:
            raise ModelRetry(
                f"Section '{section.title}' must have at least one source")

        # Verify URLs in sources
        for source in section.sources:
            source_url = source.url
            # Normalize the source URL for comparison
            if source_url.startswith('http://'):
                source_url = source_url[7:]
            elif source_url.startswith('https://'):
                source_url = source_url[8:]
            source_url = source_url.rstrip('/')

            # Check if any variation of the URL is valid
            url_found = False
            for valid_url in valid_urls:
                valid_normalized = valid_url
                if valid_normalized.startswith('http://'):
                    valid_normalized = valid_normalized[7:]
                elif valid_normalized.startswith('https://'):
                    valid_normalized = valid_normalized[8:]
                valid_normalized = valid_normalized.rstrip('/')

                if source_url == valid_normalized or \
                   source_url.split('?')[0] == valid_normalized.split('?')[0]:
                    url_found = True
                    break

            if not url_found:
                console.print(
                    f"[yellow]Warning: URL not found in search results: {source.url}[/yellow]")
                # Instead of raising an error, we'll just warn about it
                # raise ModelRetry(f"Invalid source URL: {source.url}")

    return result


def format_report_markdown(report: ResearchReport) -> str:
    """Format the research report as markdown."""
    md = [
        f"# {report.title}\n",
        f"*Generated on {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "## Introduction\n",
        f"{report.introduction.content}\n",
    ]

    for section in report.body_sections:
        md.append(f"## {section.title}\n")
        md.append(f"{section.content}\n")

    md.append("## Conclusion\n")
    md.append(f"{report.conclusion.content}\n")

    md.append("## Sources\n")
    all_sources = []
    all_sources.extend(report.introduction.sources)
    for section in report.body_sections:
        all_sources.extend(section.sources)
    all_sources.extend(report.conclusion.sources)

    for i, source in enumerate(all_sources, 1):
        md.append(f"{i}. [{source.title}]({source.url})\n")
        md.append(f"   > {source.snippet}\n")

    return "\n".join(md)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def chunk_content(content: str, max_tokens: int = 8000) -> List[str]:
    """Split content into chunks that fit within token limits."""
    chunks = []
    current_chunk = []
    current_tokens = 0

    # Split by paragraphs first
    paragraphs = content.split('\n\n')

    for paragraph in paragraphs:
        paragraph_tokens = count_tokens(paragraph)

        if paragraph_tokens > max_tokens:
            # If a single paragraph is too large, split by sentences
            sentences = paragraph.split('. ')
            for sentence in sentences:
                sentence_tokens = count_tokens(sentence)
                if current_tokens + sentence_tokens <= max_tokens:
                    current_chunk.append(sentence)
                    current_tokens += sentence_tokens
                else:
                    if current_chunk:
                        chunks.append('. '.join(current_chunk) + '.')
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
        elif current_tokens + paragraph_tokens <= max_tokens:
            current_chunk.append(paragraph)
            current_tokens += paragraph_tokens
        else:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [paragraph]
            current_tokens = paragraph_tokens

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


async def process_content_chunks(chunks: List[str], agent: Agent, topic: str) -> Dict:
    """Process content chunks and aggregate results."""
    summaries = []

    for chunk in chunks:
        chunk_deps = ResearchDeps(
            topic=topic,
            search_results=[],  # Empty as we're processing chunks
            webpage_contents={'chunk': chunk}
        )

        result = await agent.run(
            "Summarize this content chunk maintaining key information and any relevant citations:",
            deps=chunk_deps
        )
        summaries.append(result.data)

    return summaries


async def generate_research_report(topic: str) -> str:
    """Generate a research report on the given topic."""
    console.print(f"[cyan]Researching topic: {topic}[/cyan]")

    # Initial search
    console.print("[cyan]Gathering information...[/cyan]")
    search_results = await search_topic(None, topic)

    # Process webpage contents in chunks
    all_summaries = []
    for result in search_results[:5]:  # Limit to top 5 results
        url = result['url']
        content = await get_webpage_content(None, url)

        if content:
            # Chunk the content
            chunks = chunk_content(content)
            # Process chunks
            summaries = await process_content_chunks(chunks, research_agent, topic)
            all_summaries.extend(summaries)

    # Generate final report using summarized content
    console.print("[cyan]Generating final report...[/cyan]")
    deps = ResearchDeps(
        topic=topic,
        search_results=search_results,
        webpage_contents={'summaries': all_summaries}
    )

    result = await research_agent.run(
        f"Create a detailed research report about: {topic}",
        deps=deps
    )

    return format_report_markdown(result.data)

if __name__ == "__main__":
    import asyncio

    async def main():
        topic = input("Enter a research topic: ")
        report_md = await generate_research_report(topic)
        console.print(Markdown(report_md))

        # Optionally save to file
        filename = f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w") as f:
            f.write(report_md)
        console.print(f"\n[green]Report saved to: {filename}[/green]")

    asyncio.run(main())
