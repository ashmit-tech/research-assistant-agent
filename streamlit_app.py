"""Streamlit interface for the Research Assistant."""

import os
import asyncio
from datetime import datetime
from pathlib import Path

import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.colored_header import colored_header
from rich.console import Console

from research_assistant import generate_research_report

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
</style>
""", unsafe_allow_html=True)


class StreamlitConsole(Console):
    """Custom console that redirects output to Streamlit."""

    def print(self, *args, **kwargs):
        style = kwargs.get('style', '')
        message = ' '.join(str(arg) for arg in args)

        if 'red' in style:
            st.error(message)
        elif 'yellow' in style:
            st.warning(message)
        elif 'green' in style:
            st.success(message)
        elif 'cyan' in style:
            with st.status(message, expanded=True) as status:
                status.update(label=message, state="running")
                yield status
        else:
            st.write(message)


def create_download_link(content, filename):
    """Create a download link for the report."""
    st.download_button(
        label="📥 Download Report",
        data=content,
        file_name=filename,
        mime="text/markdown",
    )


def main():
    # Header
    colored_header(
        label="AI Research Assistant 📚",
        description="Generate comprehensive research reports on any topic",
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
        - Well-structured format
        """)
        add_vertical_space(2)

        st.markdown("### Features")
        st.markdown("""
        - Comprehensive research
        - Automatic citations
        - Markdown formatting
        - Downloadable reports
        """)

    # Main content
    topic = st.text_input(
        "Enter your research topic:",
        placeholder="e.g., The impact of artificial intelligence on healthcare",
        help="Enter any topic you want to research about",
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        generate = st.button(
            "🔍 Generate Report",
            type="primary",
            disabled=not topic,
            help="Click to generate a detailed research report",
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

            # Generate report
            with st.status("Generating report...", expanded=True) as status:
                # Run the async function
                report_md = asyncio.run(generate_research_report(topic))
                status.update(
                    label="Report generated successfully!", state="complete")

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{timestamp}.md"
            filepath = reports_dir / filename
            with open(filepath, "w") as f:
                f.write(report_md)

            # Display report
            st.markdown('<div class="research-report">',
                        unsafe_allow_html=True)
            if show_raw:
                st.markdown("```markdown" + report_md + "```")
            else:
                st.markdown(report_md)
            st.markdown('</div>', unsafe_allow_html=True)

            # Download section
            st.markdown('<div class="report-download">',
                        unsafe_allow_html=True)
            st.markdown("### Download Report")
            create_download_link(report_md, filename)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please try again or contact support if the problem persists.")


if __name__ == "__main__":
    main()
