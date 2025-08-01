from pathlib import Path
from typing import override
import streamlit as st
from core.prompts_manager.prompt_manager import promptManager

class XSLTMigratorPromptManager(promptManager):
    def __init__(self):
        super().__init__()
        
    def load_default_prompts(self):
        pass
    
    @override
    def load_prompts(self, params):
        pass

    def load_prompts_to_simplify_xslt(self, params):
        system_prompts = []
        system_prompts.append({"role": "system", "content": """You are a helpful assistant and expert in XSLT. 
                               Your task is to simplify the given XSLT to a more readable format. 
                               Do not use the current variable names. Attributes must not be mentioned seperately but instead with the parent node. 
                               Return only the XSLT in the response. Do not add any other text, other than XSLT in response (No enclosing on triple ` and extra words like 'XSLT').
                               Use output encoding=UTF-8 and use xsl:template='/'. indent=yes."""})
        system_prompts.append({"role": "user", "content": f"The input XSLT, enclosed in triple -. ---{params.get("xslt")}---"})
        self.agent.set_prompts(system_prompts)
               
    def load_prompts_to_generate_specs(self, params):
        system_prompts = []
        system_prompts.append({"role": "system", "content": """You are a helpful assistant and expert in XSLT. 
                               Your task is to generate a markdown file for the given XSLT following the below format:
                                <index>. Input: <input xpath>
                                    Output: <output xpath>
                                    Remarks: <any logic required to generate the output>
                                Repeat for all nodes in the above format.
                                If the ouput is hardcoded, mention Input as NA and Remarks as Hardcoded as <value>.
                                If the ouput is directly mapped from input, mention Remarks as NA.
                                Return only the markdown in the response. Do not add any other text, other than markdown in response (No enclosing on triple ` and extra words like 'Markdown')."""})
        system_prompts.append({"role": "user", "content": f"The input XSLT, enclosed in triple -. ---{params.get("xslt")}---"})
        self.agent.set_prompts(system_prompts)
    
    def load_prompts_to_display_specs_in_html(self, params):
        system_prompts = []
        # Enforce the root element to be whatever the user chooses.
        system_prompts.append({"role": "user", "content": """You are a helpful assistant and expert in analysing markdown files. 
                               Your task is to generate a HTML file for the given Markdown creating three columns for Input, Output and Remarks. indent=yes.
                               Return only the HTML in the response. Do not add any other text, other than HTML in response (No enclosing on triple ` and extra words like 'HTML')."""})
        system_prompts.append({"role": "user", "content": f"The input Markdown, enclosed in triple -. ---{params.get("specs")}---"})
        self.agent.set_prompts(system_prompts)
        
    def get_default_system_prompt(self):
        try:
            # Resolve the file path
            file_path = Path(__file__).resolve().parent / "../config/prompts/generic/default_system_prompt_for_xslt_migrator.md"
            
            # Read the file content
            with file_path.open('r', encoding='utf-8') as file:
                initial_prompt = file.read().strip()
            
            
            return {'role': 'system', 'content': initial_prompt}
        except FileNotFoundError:
            st.error(f"Default system prompts file not found: {file_path}")
        except IOError as e:
            st.error(f"Error reading default system prompts file: {e}")
        
        return None