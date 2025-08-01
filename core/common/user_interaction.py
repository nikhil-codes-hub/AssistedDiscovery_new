import streamlit as st

class userInteraction:
    """
    A class to manage user interactions and session state initialization in a Streamlit application.
    """

    @staticmethod
    def write_chat_message(role, message, spinner_with_message=None):
        """
        Writes a chat message to the Streamlit interface with an optional spinner.

        Args:
            role (str): The role of the message sender ('user' or 'assistant').
            message (str): The content of the message.
            spinner_with_message (str, optional): The spinner message to display while rendering.
        """
        avatar = "😎" if role == 'user' else "🤖"

        if spinner_with_message:
            with st.chat_message(role, avatar=avatar):
                with st.spinner(spinner_with_message):
                    st.markdown(message)
        else:
            with st.chat_message(role, avatar=avatar):
                st.markdown(message)

        st.session_state.messages.append({"role": role, "content": message})

    @staticmethod
    def add_to_prompts(prompt):
        """
        Adds a prompt to the session state and updates the generator agent if available.

        Args:
            prompt (dict): The prompt to add.
        """
        st.session_state.prompts.append(prompt)
        if st.session_state.generator_agent is not None:
            st.session_state.generator_agent.add_message(prompt)

    @staticmethod
    def add_to_messages(message):
        """
        Adds a user message to the session state.

        Args:
            message (str): The user message to add.
        """
        st.session_state.messages.append({"role": "user", "content": message})

    @staticmethod
    def init_objects_into_session():
        """
        Initializes default objects into the Streamlit session state.
        """
        session_defaults = {
            "active_llm_context": None,
            "messages": [],
            "prompts": [],
            "xslt": None,
            "generated_xslt": None,
            "existing_xslt": None,
            "updated_xslt": None,
            "existing_specs": None,
            "updated_specs": None,
            "source_xml": None,
            "target_xml": None,
            "llm_target_xml": None,
            "specs_file": None,
            "cook_books": None,
            "questions_map": {},
            "has_human_feedback": False,
            "generator_agent": None,
            "ask_yes_no": False,
            "user_response": None,
            "chat_history": [],
            "updated_specs": None,
            "markdown_spec": None,
            "url": None,
            "current_xslt": None,
            "space":None,
            "page_name":None,
            "html":None,
            "gpt_model_used": None,
            "number_of_calls_to_llm": 0,
            "total_cost_per_tool": 0,
            "tags_to_select": {},
            "pattern_responses": {},
            "insights": None,
            
        }

        for key, value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
