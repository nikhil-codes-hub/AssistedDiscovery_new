import streamlit as st
import pandas as pd
import os
import sys
import re
import json
from core.assisted_discovery.gap_analysis_manager import GapAnalysisManager
from core.common.ui_utils import render_custom_table
from core.prompts_manager.gap_analysis_prompt_manager import GapAnalysisPromptManager
from core.database.sql_db_utils import SQLDatabaseUtils

class PatternIdentifyManager(GapAnalysisManager, GapAnalysisPromptManager):

    def __init__(self, model_name, db_utils=None):
        super().__init__(model_name)
        self.db_utils = db_utils if db_utils else SQLDatabaseUtils()
    
    def verify_and_confirm_airline(self, unknown_source_xml_content, selected_airlines):
        with st.spinner(":rainbow[Genie is analyzing the API, please wait...]"):
            sections = self.db_utils.list_main_elements(unknown_source_xml_content)
            gap_analysis = {
                "sections": [],
                "matched_airlines": set()
            }

            for section in sections:
                row = self.db_utils.search_in_database(section, selected_airlines)
                if row:
                    section_data = {
                        "sectionName": section,
                        "rules": []
                    }

                    for item in row:
                        rule = {
                            "airline": item[0],
                            "apiVersion": item[1],
                            "verificationRule": item[2],
                            "matched": False,
                            "reason": ""
                        }

                        search_prompt = item[3]
                        response_obj_json = self.identify_patterns_in_unknown_source_xml(unknown_source_xml_content, search_prompt)
                        confirmation = response_obj_json.get('confirmation')
                        rule["matched"] = confirmation == "YES"
                        if rule["matched"] == True:
                            gap_analysis["matched_airlines"].add(item[0])
                        rule["reason"] = response_obj_json.get('reason', "")

                        section_data["rules"].append(rule)

                    gap_analysis["sections"].append(section_data)

            return gap_analysis


    def identify_patterns_in_unknown_source_xml(self, unknown_source_xml_content, search_prompt):
        self.load_prompts_for_pattern_identification(unknown_source_xml_content, search_prompt)
        response = self._initiate_conversation()
        response_obj = re.sub(r'[\x00-\x1F\x7F]', '', response)
        response_obj_json = json.loads(response_obj)
        return response_obj_json

    def display_api_analysis(self, data):
        sections = data.get('sections', [])
        matched_airlines = data.get('matched_airlines', [])
        rows = []
        for section in sections:
            section_name = section.get('sectionName')
            rules = section.get('rules', [])
            for rule in rules:
                rows.append({
                    'API Version': rule.get('apiVersion'),
                    'Section': section_name,
                    'Validation Rule': rule.get('verificationRule'),
                    'Verified': 'Yes' if rule.get('matched') else 'No',
                    'Reason': rule.get('reason')
                })
        df = pd.DataFrame(rows)
        
        # Sort to show verified "Yes" entries first
        if not df.empty:
            df = df.sort_values('Verified', ascending=False)

        if df.empty:
            st.markdown(":red[No validation rules found.]", unsafe_allow_html=True)
        else:
            df = df.reset_index(drop=True)
            long_text_cols = ['Validation Rule', 'Reason']
            from core.common.css_utils import get_css_path
            css_path = get_css_path()
            render_custom_table(df, long_text_cols, css_path)
        
        st.subheader("Matched Airline(s):")
        if matched_airlines:
            st.markdown(
                f'<span style="background-color:#ffe066; color:#222; font-weight:bold; padding:4px 8px; border-radius:5px;">'
                + ", ".join(matched_airlines) + '</span>', unsafe_allow_html=True
            )
        else:
            st.markdown(":red[No airline(s) matched.]", unsafe_allow_html=True)