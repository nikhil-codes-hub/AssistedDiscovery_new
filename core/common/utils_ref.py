import streamlit as st
import pandas as pd
import difflib
import re
from lxml import etree
import html2text
from bs4 import BeautifulSoup
from io import StringIO
from llama_index.core import Document
import html
from typing import List, Dict, Tuple, Optional, Union

class MarkdownProcessor:
    """Handles all markdown processing operations."""
    
    @staticmethod
    def convert_html_to_markdown(html_content: str) -> str:
        """Convert HTML content to markdown format."""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        return h.handle(html_content)
    
    @staticmethod
    def refine_and_display_markdown_update(markdown_content: str) -> str:
        """Refine markdown content for display in update view."""
        lines = markdown_content.split('\n')
        modified_content = []
        
        for line in lines[2:]:
            columns = line.split('| ')
            if len(columns) >= 3:
                input_value = columns[1].strip()
                output_value = columns[2].strip()
                remarks = columns[3].strip()
                field_type = columns[4].strip()[:-1]
                
                modified_line = []
                if input_value and input_value != "NA":
                    modified_line.append(f"Input: {input_value}")
                if output_value and output_value != "NA":
                    modified_line.append(f"Output: {output_value}")
                if remarks and remarks != "NA":
                    modified_line.append(f"Remarks: {remarks}")
                if field_type and field_type != "NA":
                    modified_line.append(f"Type: {field_type}")
                    
                modified_content.append(", ".join(modified_line))
            else:
                modified_content.append(line)
                
        return '\n'.join(modified_content)
    
    @staticmethod
    def refine_and_display_markdown(markdown_content: str) -> Tuple[str, List[Document]]:
        """Refine markdown content and convert to document format."""
        lines = markdown_content.split('\n')
        start_index = next((i + 1 for i, item in enumerate(lines) 
                          if item.strip().startswith(('|:---', '|---'))), 0)
        
        modified_content = []
        for line in lines[start_index:]:
            if not line:
                continue
                
            columns = line.split('|')
            if len(columns) >= 3:
                input_value = columns[2].strip()
                output_value = columns[3].strip()
                remarks = columns[6].strip()
                
                parts = []
                parts.append(f"Input Xpath: {input_value if input_value and input_value != 'NA' else 'NA'}")
                
                if output_value and output_value != "NA":
                    parts.append(f"Output Xpath: {output_value}")
                if remarks and remarks != "NA":
                    parts.append(f"Description: {remarks}")
                    
                modified_content.append(", ".join(parts))
        
        vector_documents = [Document(text=doc) for doc in modified_content]
        return '\n'.join(modified_content), vector_documents


class XMLProcessor:
    """Handles XML processing operations."""
    
    @staticmethod
    def refine_xslt(xslt_content: str) -> str:
        """Pretty print XSLT content."""
        xslt_tree = etree.XML(xslt_content)
        return etree.tostring(xslt_tree, pretty_print=True).decode()
    
    @staticmethod
    def compare_xmls(xml1: str, xml2: str) -> Tuple[str, float]:
        """Compare two XML strings and return diff HTML and match percentage."""
        xml1_normalized = XMLProcessor.normalize_xml(xml1)
        xml2_normalized = XMLProcessor.normalize_xml(xml2)
        
        diff = difflib.HtmlDiff().make_table(
            xml1_normalized, 
            xml2_normalized, 
            "Source XML", 
            "Target XML", 
            context=True
        )
        
        matcher = difflib.SequenceMatcher(None, xml1_normalized, xml2_normalized)
        match_percentage = matcher.ratio() * 100
        return diff, match_percentage
    
    @staticmethod
    def normalize_xml(xml_string: str) -> List[str]:
        """Normalize XML string for comparison."""
        xml_clean = XMLProcessor.remove_encoding_declaration(xml_string)
        parser = etree.XMLParser(remove_blank_text=True)
        xml_tree = etree.fromstring(xml_clean.encode('utf-8'), parser)
        pretty_xml = etree.tostring(xml_tree, pretty_print=True).decode('utf-8')
        return pretty_xml.strip().splitlines()
    
    @staticmethod
    def remove_encoding_declaration(xml_string: str) -> str:
        """Remove XML encoding declaration from string."""
        return re.sub(r'<\?xml.*?\?>', '', xml_string)


class HTMLProcessor:
    """Handles HTML processing operations."""
    
    @staticmethod
    def convert_html_to_csv(html_content: str) -> Tuple[str, pd.DataFrame]:
        """Convert HTML table to CSV format."""
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find("table")
        
        if not table:
            return "", pd.DataFrame()
            
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = []
        
        for tr in table.find_all("tr")[1:]:
            rows.append([td.get_text(strip=True) for td in tr.find_all("td")])
        
        df = pd.DataFrame(rows, columns=headers)
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        return csv_buffer.getvalue(), df
    
    @staticmethod
    def markdown_to_html_table(md_str: Union[str, List[Dict]]) -> str:
        """Convert markdown string or list of dicts to HTML table."""
        headers = ["Input", "Output", "Remarks", "Type"]
        html_rows = ['<table data-table-width="1800" data-layout="full-width">']
        html_rows.append('<tr>' + ''.join(f'<th><p>{h}</p></th>' for h in headers) + '</tr>')
        
        if isinstance(md_str, str):
            field_pattern = re.compile(
                r'(Input|Output|Remarks|Type):\s*(.*?)'
                r'(?=,(?:\s*)(?:Input|Output|Remarks|Type):|$)',
                re.IGNORECASE
            )
            for row in md_str.strip().split('\n'):
                matches = field_pattern.findall(row)
                field_map = {k.capitalize(): v.strip() for k, v in matches}
                values = [html.escape(field_map.get(h, '')) for h in headers]
                html_rows.append('<tr>' + ''.join(f'<td><p>{v}</p></td>' for v in values) + '</tr>')
        elif isinstance(md_str, list):
            for entry in md_str:
                values = [html.escape(str(entry.get(h) or entry.get(h.lower()) or '')) for h in headers]
                html_rows.append('<tr>' + ''.join(f'<td><p>{v}</p></td>' for v in values) + '</tr>')
        else:
            html_rows.append('<tr><td colspan="4"><p>Invalid specifications format</p></td></tr>')
            
        html_rows.append('</table>')
        return '\n'.join(html_rows)


class StreamlitUI:
    """Handles Streamlit UI components and state management."""
    
    @staticmethod
    def get_comparison_style():
        """Use the StreamlitUI class to get comparison styles."""
        return """
            <style>
                table {
                    width: 120%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    word-break: break-word;
                    white-space: pre-wrap;
                }
                td:nth-child(2), th:nth-child(2) {
                    width: 5%;
                    min-width: 25px;
                }
                td:nth-child(5), th:nth-child(5) {
                    width: 5%;
                    min-width: 25px;
                }
            </style>
            """

    @staticmethod
    def inject_custom_css() -> None:
        """Inject custom CSS for the Streamlit app."""
        st.markdown("""
            <style>
            .stDownloadButton button {
                background-color: #007bff;
                color: white;
            }
            .diff_add { background-color: #ccffcc; }  /* Green background for additions */
            .diff_sub { background-color: #ffcccc; }  /* Red background for deletions */
            table { width: 100%; }                    /* Full width table */
            td { padding: 8px; border: 1px solid #ddd; } /* Table cell styling */
            </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_messages() -> None:
        """Display chat messages from session state."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    @staticmethod
    def display_generated_xslt() -> None:
        """Display generated XSLT with download option."""
        st.title("Generated XSLT")
        output_placeholder = st.empty()
        updated_xslt = st.session_state.get('updated_xslt')
        
        if updated_xslt:
            height = min(400, len(updated_xslt) * 30)
            output_placeholder.text_area("", updated_xslt, height)
            st.download_button(
                label="Download XSLT", 
                data=updated_xslt, 
                file_name="updated_xslt.xslt", 
                mime="application/xslt"
            )
        else:
            height = min(100, 200)
            output_placeholder.markdown(
                f'<div style="border: 1px solid #3c3c73; padding: 10px; height: {height}px; '
                'overflow-y: auto;">XSLT will appear here</div>', 
                unsafe_allow_html=True
            )
    
    @staticmethod
    def display_generated_specs() -> None:
        """Display generated specifications with download option."""
        st.title("Generated specs")
        output_placeholder = st.empty()
        generated_specs = st.session_state.get('updated_specs')
        
        if generated_specs:
            height = min(400, len(generated_specs) * 30)
            output_placeholder.text_area("", generated_specs, height)
            st.download_button(
                label="Download Specs", 
                data=generated_specs, 
                file_name="generated_specs.txt", 
                mime="text/plain"
            )
        else:
            height = min(100, 200)
            output_placeholder.markdown(
                f'<div style="border: 1px solid #3c3c73; padding: 10px; height: {height}px; '
                'overflow-y: auto;">Specs will appear here</div>', 
                unsafe_allow_html=True
            )


# Module-level utility functions
def extract_space_and_page_name(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract space and page name from Confluence URL."""
    try:
        parts = url.split('/')
        space_index = parts.index('spaces') + 1
        space = parts[space_index]
        page_name = parts[-1]
        return space, page_name
    except (ValueError, IndexError):
        return None, None


# Initialize Streamlit UI components
StreamlitUI.inject_custom_css()
