import os
from typing import List
from datetime import datetime
from pathlib import Path

import logfire
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tavily import TavilyClient
from rich.console import Console
from rich.markdown import Markdown

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

# Load environment variables
load_dotenv()

# Configure logging
logfire.configure(send_to_logfire='if-token-present')

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
console = Console()

# Configure DeepSeek Resonater model
model = OpenAIModel(
    'deepseek-chat',
    provider=OpenAIProvider(
        base_url='https://api.deepseek.com',  
        api_key=os.getenv('DEEPSEEK_API_KEY')
    ),
)

# Data Models
class Source(BaseModel):
    """A source used in the research."""
    title: str
    url: str
    snippet: str = Field(description="A relevant quote or summary from the source")

class ResearchSection(BaseModel):
    """A section of the research report."""
    title: str
    content: str
    sources: List[Source]

class ResearchReport(BaseModel):
    """The complete research report."""
    title: str
    introduction: ResearchSection
    body_sections: List[ResearchSection]
    conclusion: ResearchSection
    timestamp: datetime = Field(default_factory=datetime.now)

class ResearchDeps(BaseModel):
    """Dependencies for the research agent."""
    topic: str
    search_results: List[dict]

# Define the Research Agent
research_agent = Agent(
    model,
    deps_type=ResearchDeps,
    result_type=ResearchReport,
    retries=3,
    system_prompt=f"""You are an expert research assistant. Your task is to create detailed, 
    well-structured research reports on any given topic. 
    
    CRITICAL SOURCE REQUIREMENTS:
    1. You MUST ONLY use URLs that are EXACTLY as they appear in the search_results.
    2. DO NOT modify, generate, or create any URLs - use them exactly as provided.
    3. DO NOT use future dates or hypothetical sources.
    4. Each section must include at least one valid source from the search results.
    5. If you cannot find enough valid sources, make the section shorter or combine sections.
    
    Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Follow these guidelines:
    1. Create clear, engaging titles
    2. Write comprehensive introductions that outline the scope
    3. Organize the body into logical sections based on available sources
    4. Draw meaningful conclusions
    5. Use markdown formatting for better readability
    6. Consider the current date when discussing events
    7. Keep sections focused on information that has valid sources
    """
)

@research_agent.tool
async def search_topic(ctx: RunContext[ResearchDeps], query: str) -> List[dict]:
    """Search for information about the topic using Tavily."""
    search_response = tavily_client.search(query=query, search_depth="advanced", max_results=10)
    return search_response['results']

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
    all_sources = report.introduction.sources + sum([section.sources for section in report.body_sections], []) + report.conclusion.sources
    for i, source in enumerate(all_sources, 1):
        md.append(f"{i}. [{source.title}]({source.url})\n")
        md.append(f"   > {source.snippet}\n")
    return "\n".join(md)

async def generate_research_report(topic: str) -> str:
    """Generate a research report on the given topic."""
    try:
        search_results = await search_topic(None, topic)
        deps = ResearchDeps(topic=topic, search_results=search_results)
        report = await research_agent.run(f"Create a detailed research report about: {topic}", deps=deps)
        return format_report_markdown(report.data)
    except Exception as e:
        console.print(f"[red]Error generating research report: {str(e)}[/red]")
        return f"Error generating research report: {str(e)}"

if __name__ == "__main__":
    import asyncio
    async def main():
        topic = input("Enter a research topic: ")
        report_md = await generate_research_report(topic)
        console.print(Markdown(report_md))
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = reports_dir / f"research_report_{timestamp}.md"
        with open(filepath, "w") as f:
            f.write(report_md)
    asyncio.run(main())
