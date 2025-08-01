from pathlib import Path
from core.prompts_manager.prompt_manager import promptManager
import streamlit as st

class XSLTUpdatePromptManager(promptManager):
    """
    A manager class for handling prompts related to XSLT updates.
    """

    def load_default_prompts(self, params):
        """
        Loads the default system prompts for updating XSLT.

        Args:
            params (dict): A dictionary containing parameters such as 'source_xml', 'xslt', and 'specs_file'.

        Returns:
            list: A list of system and user prompts based on the provided parameters.
        """
        xslt = params.get("xslt")
        specs_file = params.get("specs_file")
        user_requirement_prompt = params.get("user_requirement_prompt")

        # Base system prompts
        system_prompts = [
            self.get_default_system_prompt(),
            {"role": "system", "content": "Ignore any blocks of code that are enclosed within <!--Manual change-->."},
            {"role": "user", "content": f"The existing XSLT, enclosed in triple ^. ^^^{xslt}^^^"},
            {"role":"user", "content": "The user instruction to update the XSLT:" + user_requirement_prompt}
        ]
        
        if st.session_state.active_llm_context == "UPDATE_XSLT":
            system_prompts += [{"role":"user", "content": "Return only JSON with 'updated_XSLT'."}]

        # Add prompts for specs_file if provided
        if specs_file:
            system_prompts += [
                {"role": "system", "content": "For attributes and elements if optional use an if test."},
                {"role": "user", "content": f"Here are the specifications:\n{specs_file}"}
            ]

        return system_prompts
    
    def load_prompts(self, params):
        """
        Combines default system prompts, user instructions, and cookbook content into a single list of prompts.

        Args:
            params (dict): A dictionary containing parameters such as 'user_requirement_prompt', 'cook_books', 'source_xml', 'xslt', and 'specs_file'.

        Returns:
            list: A combined list of prompts including system prompts, user instructions, and cookbook content.
        """
        user_requirement_prompt = params["user_requirement_prompt"]
        cookBooks = self.loadCookBooks()
        system_prompts = self.load_default_prompts(params)
        
        # Add additional instructions
        combined_prompts = system_prompts + [
            {"role": "user", "content": f"The user instruction to update the XSLT {user_requirement_prompt}"},
            {"role": "user", "content": "DO NOT ADD ANY OTHER TEXT, OTHER THAN JSON IN RESPONSE (No enclosing on triple ` and extra words like 'JSON')."}  
        ]
        if st.session_state.active_llm_context == "UPDATE_XSLT":
            combined_prompts += [{"role": "user", "content": cookBooks}]
            combined_prompts += [{"role":"user",  "content": "Return only JSON with 'updated_XSLT'."}]
        if st.session_state.active_llm_context == "UPDATE_SPECS":
            combined_prompts.append({"role":"user", "content": "Update the specification file based on user requirement : " + user_requirement_prompt})
            combined_prompts.append({
                "role":"system",
                "content": 
                    "Your reply must be exactly a JSON object with one field:\n"
                    "{\n"
                    '  "updated_specs": "<the entire spec file as one JSON string>"\n'
                    "}\n\n"
                    "Example:\n"
                    '{\n'
                    '  "updated_specs": "Input: , Output: OrderCreateRQ/@Version, Remarks: Hardcoded as 17.2, \nType: Attribute\nInput: Request/Context/correlationid, Output: OrderCreateRQ/@Correlationid, Remarks: Optional, Type: \nInput: Request/Context/correlationID, Output: OrderCreateRQ/@TransactionIdentifier, Remarks: Optional, Type: \n'
                    "}"
            })
        self.agent.set_prompts(combined_prompts)
    
    def get_default_system_prompt(self):
        """
        Retrieves the default system prompt from a predefined file.

        Returns:
            dict: A dictionary containing the role ('assistant') and content of the default system prompt.
            None: If the file is not found or cannot be read.
        """
        try:
            # Resolve the file path
            file_path = Path(__file__).resolve().parent / "../config/prompts/generic/default_system_prompts_for_update.txt"
            
            # Read the file content
            with file_path.open('r', encoding='utf-8') as file:
                initial_prompt = file.read().strip()
            
            return {'role': 'assistant', 'content': initial_prompt}
        except FileNotFoundError:
            st.error(f"Default system prompts file not found: {file_path}")
        except IOError as e:
            st.error(f"Error reading default system prompts file: {e}")
        
        return None
        
    def loadCookBooks(self):
        """
        Loads all cookbook instructions from the specified directory and stores them in the session state.

        Returns:
            str: Combined content of all cookbook files, including file names as headers.
        """
        try:
            # Resolve the directory path
            current_dir = Path(__file__).resolve().parent
            directory_path = current_dir / "../../config/cookbooks"
            cook_books = "Cook-book instructions:\n"

            # Check if the directory exists
            if directory_path.exists():
                for file_path in directory_path.rglob("*"):  # Recursively find all files
                    if file_path.is_file():
                        with file_path.open('r', encoding='utf-8') as f:
                            cook_books += f"\n--- {file_path.name} ---\n"  # Add file name as a header
                            cook_books += f.read().strip() + "\n"

            return cook_books

        except Exception as e:
            st.error(f"Error loading cookbooks: {e}")
            return "Error loading cookbooks."