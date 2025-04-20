import os
from typing import List
from datetime import datetime
from pathlib import Path

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

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
console = Console()  # This will be overridden by StreamlitConsole when needed

# Configure DeepSeek Resonater model
model = OpenAIModel(
    'deepseek-chat',
    provider=OpenAIProvider(
        base_url='https://api.deepseek.com',  
        api_key=os.getenv('DEEPSEEK_API_KEY')
    )
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
    system_prompt=f"""You are an expert research assistant. Your task is to create EXTREMELY COMPREHENSIVE, DETAILED, 
    and LENGTHY research reports on any given topic. Your reports should be ACADEMIC in quality and 
    EXHAUSTIVE in coverage. AIM FOR AT LEAST 8-10 PAGES of DENSE, SUBSTANTIVE CONTENT.
    
    CRITICAL SOURCE REQUIREMENTS:
    1. You MUST ONLY use URLs that are EXACTLY as they appear in the search_results.
    2. DO NOT modify, generate, or create any URLs - use them exactly as provided.
    3. DO NOT use future dates or hypothetical sources.
    4. Each section must include at least one valid source from the search results.
    5. If you cannot find enough valid sources, make the section shorter or combine sections.
    
    Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    REQUIRED REPORT LENGTH AND STRUCTURE:
    1. Create a compelling, detailed title (10-15 words)
    2. Write an extensive introduction (500+ words) that thoroughly outlines the scope, significance, and context
    3. Organize the body into AT LEAST 8-12 SUBSTANTIVE SECTIONS with detailed subheadings
       - Each section MUST BE AT LEAST 400-600 words - NO EXCEPTIONS
       - MANDATORY SECTIONS to include (adapt as needed for topic):
         * Historical Background and Evolution
         * Current State of the Art/Knowledge
         * Key Theoretical Frameworks
         * Methods and Approaches
         * Major Challenges and Limitations
         * Case Studies and Real-World Applications
         * Comparative Analysis
         * Controversies and Debates
         * Future Directions and Implications
       - Go into EXTREME DEPTH on each section - provide extensive details, examples, and analysis
    4. Write a substantial conclusion (500+ words) that synthesizes findings and explores implications
    5. Use professional academic style throughout, with proper citations
    
    CONTENT REQUIREMENTS:
    1. Include specific statistics, data points, and quantitative information wherever possible
    2. Provide multiple expert perspectives and competing viewpoints
    3. Analyze the topic from multiple angles (historical, technological, ethical, economic, social, etc.)
    4. Use rich, precise language with field-specific terminology appropriate to academic writing
    5. Structure content with clear paragraph breaks, topic sentences, and transitions
    6. Use markdown formatting effectively for improved readability

    LENGTH IS CRITICAL: Push the model to its limits. Create the LONGEST, MOST COMPREHENSIVE report possible
    while maintaining quality and coherence. The goal is to produce a report that would be suitable for
    publication in an academic journal or as a comprehensive industry whitepaper.
    """
)

@research_agent.tool
async def search_topic(ctx: RunContext[ResearchDeps], query: str) -> List[dict]:
    """Search for information about the topic using Tavily."""
    # First search for general information
    primary_search = tavily_client.search(
        query=query, 
        search_depth="advanced", 
        max_results=18,
        include_answer=True,
        include_raw_content=False
    )
    
    # Additional searches for more depth - but fewer subtopics
    subtopics = [
        f"{query} background and history",
        f"{query} latest developments",
        f"{query} analysis and perspectives",
        f"{query} future implications",
        f"{query} methodology and research",
        f"{query} case studies and examples",
        f"{query} critical perspectives",
    ]
    
    all_results = primary_search['results']
    
    # Collect additional results from subtopic searches (fewer per subtopic)
    for subtopic in subtopics:
        try:
            console.print(f"[blue]Searching for subtopic: {subtopic}[/blue]")
            additional_results = tavily_client.search(
                query=subtopic,
                search_depth="advanced",
                max_results=5,
                include_raw_content=False
            )
            all_results.extend(additional_results['results'])
        except Exception as e:
            console.print(f"[red]Error searching for subtopic {subtopic}: {str(e)}[/red]")
    
    # Process results to reduce token count but keep essential information
    processed_results = []
    for i, result in enumerate(all_results):
        # Skip duplicate URLs
        if any(r.get('url') == result.get('url') for r in processed_results):
            continue
            
        # Keep only essential fields and truncate content based on position
        # Keep more content from the first results (likely more relevant)
        content_limit = 800 if i < 10 else 500
        snippet_limit = 250 if i < 10 else 150
        
        processed_result = {
            'title': result.get('title', ''),
            'url': result.get('url', ''),
            'content': result.get('content', '')[:content_limit] if result.get('content') else '',
            'snippet': result.get('snippet', '')[:snippet_limit] if result.get('snippet') else ''
        }
        processed_results.append(processed_result)
    
    console.print(f"[green]Total sources collected: {len(processed_results)}[/green]")
    return processed_results[:45]  # Limit to top 45 sources to control token count

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
        console.print(f"[bold blue]Researching topic: {topic}[/bold blue]")
        console.print("[yellow]This will generate a comprehensive research report. Please be patient as this may take several minutes...[/yellow]")
        
        search_results = await search_topic(None, topic)
        deps = ResearchDeps(topic=topic, search_results=search_results)
        
        console.print("[bold green]Sources collected. Generating report...[/bold green]")
        
        report = await research_agent.run(
            f"""Create an extremely detailed and comprehensive research report about: {topic}.
            CRITICAL: Make this report as LONG and THOROUGH as possible while maintaining quality.
            Aim for at least 8-10 pages of dense content. Each section should be at least 400-600 words.
            """,
            deps=deps
        )
        
        console.print("[bold green]Report generated! Formatting output...[/bold green]")
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
