"""Streamlit interface for the Research Assistant."""

import os
import asyncio
import re
import sys
from datetime import datetime
from pathlib import Path
import traceback

import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.colored_header import colored_header
from rich.console import Console

# Import the research assistant with console override
import research_assistant
from research_assistant import generate_research_report, tavily_client

# Configure page
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📚",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .stProgress .st-bo {
        background-color: #1e90ff;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .research-report {
        padding: 2rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .report-download {
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e9ecef;
    }
    .source-item {
        margin-bottom: 1rem;
        border-left: 3px solid #1e90ff;
        padding-left: 1rem;
    }
    .source-quote {
        font-style: italic;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)


class StreamlitConsole:
    """Simplified console that redirects output to Streamlit."""
    
    def __init__(self, status_widget=None):
        self.status_widget = status_widget
        
    def print(self, *args, **kwargs):
        if not args:
            return
            
        message = ' '.join(str(arg) for arg in args)
        style = kwargs.get('style', '')
        
        if self.status_widget:
            if isinstance(style, str) and 'red' in style:
                st.error(message)
            elif isinstance(style, str) and 'yellow' in style:
                with self.status_widget:
                    st.warning(message)
            elif isinstance(style, str) and 'green' in style:
                with self.status_widget:
                    st.success(message)
            elif isinstance(style, str) and 'blue' in style:
                with self.status_widget:
                    st.info(message)
            else:
                with self.status_widget:
                    st.write(message)
    
    def print_json(self, data=None, **kwargs):
        if self.status_widget and data:
            with self.status_widget:
                st.json(data)


def create_download_link(content, filename):
    """Create a download link for the report."""
    st.download_button(
        label="📥 Download Report",
        data=content,
        file_name=filename,
        mime="text/markdown",
    )


def format_sources_for_display(report_md):
    """Extract and format sources section for better display."""
    try:
        sources_pattern = r'## Sources\n\n(.*?)$'
        sources_match = re.search(sources_pattern, report_md, re.DOTALL)
        
        if not sources_match:
            return report_md
            
        sources_content = sources_match.group(1)
        sources_items = re.findall(r'(\d+\.\s+\[(.*?)\]\((.*?)\))\n\s+>\s+(.*?)(?=\n\d+\.|\Z)', sources_content, re.DOTALL)
        
        if not sources_items:
            return report_md
        
        formatted_sources = "## Sources\n\n"
        for item in sources_items:
            formatted_sources += f'<div class="source-item">\n'
            formatted_sources += f'{item[0]}\n'
            formatted_sources += f'<div class="source-quote">{item[3].strip()}</div>\n'
            formatted_sources += f'</div>\n\n'
        
        return report_md.replace(sources_match.group(0), formatted_sources)
    except Exception as e:
        # If any error occurs in formatting, return the original markdown
        st.warning(f"Could not format sources: {str(e)}")
        return report_md


def collect_research_data(topic, status_widget):
    """Collect research data from various sources."""
    # Manually search for results first
    with status_widget:
        st.write(f"Researching topic: {topic}")
        st.write("Collecting information from multiple sources...")
    
    # We need to call the search function directly since we're not in async context
    subtopics = [
        f"{topic} background and history",
        f"{topic} latest developments",
        f"{topic} analysis and perspectives",
        f"{topic} future implications",
        f"{topic} methodology and research",
        f"{topic} case studies and examples",
        f"{topic} critical perspectives",
    ]
    
    # First search for general information
    with status_widget:
        st.write(f"Searching for main topic information...")
    
    primary_search = tavily_client.search(
        query=topic, 
        search_depth="advanced", 
        max_results=18,
        include_answer=True,
        include_raw_content=False
    )
    
    all_results = primary_search['results']
    
    # Collect additional results from subtopic searches
    for subtopic in subtopics:
        try:
            with status_widget:
                st.info(f"Searching for subtopic: {subtopic}")
            
            additional_results = tavily_client.search(
                query=subtopic,
                search_depth="advanced",
                max_results=5,
                include_raw_content=False
            )
            all_results.extend(additional_results['results'])
        except Exception as e:
            with status_widget:
                st.error(f"Error searching for subtopic {subtopic}: {str(e)}")
    
    # Process results to reduce token count but keep essential information
    processed_results = []
    for i, result in enumerate(all_results):
        # Skip duplicate URLs
        if any(r.get('url') == result.get('url') for r in processed_results):
            continue
            
        # Keep only essential fields and truncate content based on position
        content_limit = 800 if i < 10 else 500
        snippet_limit = 250 if i < 10 else 150
        
        processed_result = {
            'title': result.get('title', ''),
            'url': result.get('url', ''),
            'content': result.get('content', '')[:content_limit] if result.get('content') else '',
            'snippet': result.get('snippet', '')[:snippet_limit] if result.get('snippet') else ''
        }
        processed_results.append(processed_result)
    
    filtered_results = processed_results[:45]  # Limit to top 45 sources
    
    with status_widget:
        st.success(f"Collected {len(filtered_results)} unique sources")
        st.write("Generating comprehensive research report...")
    
    from research_assistant import ResearchDeps
    return ResearchDeps(topic=topic, search_results=filtered_results)


def manual_generate_report(topic, deps, status_widget):
    """Call the research assistant's generate_research_report function manually."""
    with status_widget:
        st.write("Creating research report with collected information...")
    
    # Import manually to avoid circular imports
    from research_assistant import research_agent, format_report_markdown, ResearchReport
    
    # Create prompt
    prompt = f"""Create an extremely detailed and comprehensive research report about: {topic}.
    CRITICAL: Make this report as LONG and THOROUGH as possible while maintaining quality.
    Aim for at least 8-10 pages of dense content. Each section should be at least 400-600 words.
    """
    
    # Call the run method (synchronously)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(research_agent.run(prompt, deps=deps))
    loop.close()
    
    # Now access the report data safely
    if hasattr(result, 'output'):
        report_data = result.output
    else:
        report_data = result.data
    
    with status_widget:
        st.success("Report generated successfully! Formatting output...")
    
    return format_report_markdown(report_data)


def main():
    # Header
    colored_header(
        label="AI Research Assistant 📚",
        description="Generate comprehensive, academic-quality research reports on any topic",
        color_name="blue-70",
    )
    add_vertical_space(2)

    # Sidebar
    with st.sidebar:
        st.markdown("### About")
        st.markdown("""
        This AI Research Assistant helps you create detailed research reports on any topic. 
        It uses:
        - Advanced AI for analysis
        - Multiple reliable sources
        - Proper citations
        - Academic-quality writing
        - Well-structured format
        """)
        add_vertical_space(2)

        st.markdown("### Features")
        st.markdown("""
        - Comprehensive research from multiple sources
        - In-depth analysis with 8-10+ sections
        - Historical background and future implications
        - Professional academic style
        - Automatic citations and references
        - Downloadable markdown reports
        """)
        
        add_vertical_space(2)
        st.markdown("### Report Structure")
        st.markdown("""
        Each report includes:
        - Detailed introduction
        - Historical background
        - Current state analysis
        - Key theoretical frameworks
        - Methods and approaches
        - Case studies
        - Comparative analysis
        - Future implications
        - Comprehensive conclusion
        - Fully cited sources
        """)

    # Main content
    topic = st.text_input(
        "Enter your research topic:",
        placeholder="e.g., The impact of artificial intelligence on healthcare",
        help="Enter any topic you want to research about. More specific topics yield better results.",
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        generate = st.button(
            "🔍 Generate Comprehensive Report",
            type="primary",
            disabled=not topic,
            help="Click to generate a detailed research report (may take several minutes)",
        )
    with col2:
        show_raw = st.checkbox(
            "Show raw markdown",
            help="Display the raw markdown content",
        )

    if generate and topic:
        try:
            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # Initialize status
            status = st.status("Initiating research process...", expanded=True)
            
            # Override console
            original_console = research_assistant.console
            research_assistant.console = StreamlitConsole(status_widget=status)
            
            try:
                # Step 1: Collect research data
                deps = collect_research_data(topic, status)
                
                # Step 2: Generate the report
                report_md = manual_generate_report(topic, deps, status)
                
                # Mark status as complete
                status.update(label="Report generated successfully!", state="complete")
                
                # Save report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"research_report_{timestamp}.md"
                filepath = reports_dir / filename
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report_md)
    
                # Display report
                st.markdown('<div class="research-report">',
                            unsafe_allow_html=True)
                if show_raw:
                    st.code(report_md, language="markdown")
                else:
                    # Format sources for better display
                    formatted_report = format_sources_for_display(report_md)
                    st.markdown(formatted_report, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
                # Download section
                st.markdown('<div class="report-download">',
                            unsafe_allow_html=True)
                st.markdown("### Download Report")
                create_download_link(report_md, filename)
                st.markdown(f"Report saved to: {filepath}")
                st.markdown('</div>', unsafe_allow_html=True)
            finally:
                # Always restore the original console
                research_assistant.console = original_console

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            error_details = traceback.format_exc()
            st.error(f"Technical details (for debugging): {error_details}")
            st.error("Please try again or contact support if the problem persists.")


if __name__ == "__main__":
    main()
