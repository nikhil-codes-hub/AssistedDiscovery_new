import re
import json
import saxonche
from difflib import Differ
from core.llm.llm_utils import setup_agent, show_stats
from pathlib import Path
import os

class XSLTUtils:
    @staticmethod
    def apply_xslt(xslt, xml, parameters=None):
        if parameters is not None:
            xslt = XSLTUtils.replace_parameters(xslt, parameters)
        try:
            processor = saxonche.PySaxonProcessor(license=False)
            document = processor.parse_xml(xml_text=xml)
            xslt30_processor = processor.new_xslt30_processor()
            compiled_xslt = xslt30_processor.compile_stylesheet(stylesheet_text=xslt)
            transformed_xml = compiled_xslt.transform_to_string(xdm_node=document)
            return transformed_xml
        except saxonche.PySaxonApiError as e:
            raise Exception(f"An error occurred during the XSLT transformation: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    @staticmethod
    def save_generated_xslt(file_name, directory=None):
        try:
            if directory is None:
                directory = "../config/results/"
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(f"{directory}/generated_xslt.xslt", "w") as f:
                f.write(file_name)
            return file_name
        except IOError as e:
            print(f"Error writing to file: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def save_generated_xml(file_name, directory=None):
        try:
            if directory is None:
                directory = "../config/results/"
            Path(directory).mkdir(parents=True, exist_ok=True)
            with open(f"{directory}/generated_xml.xml", "w") as f:
                f.write(file_name)
            return file_name
        except IOError as e:
            print(f"Error writing to file: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def has_observations(response_obj):
        if len(response_obj['observations']) > 0:
            return True
        else:
            return False

    @staticmethod
    def consolidate_observations(response):
        print(f"In consolidate_observations::response = {response}")
        response_obj = json.loads(response)
        if XSLTUtils.has_observations(response_obj):
            formatted_observation = "Observations are:\n"
            for observation in response_obj['observations']:
                formatted_observation += observation['observation'] + "\n"
            return (True, formatted_observation)
        else:
            formatted_observation = "No observations"
            return (False, formatted_observation)

    @staticmethod
    def compare_xslt(generated_xslt, prod_xslt):
        prompt = [
            {"role": "system", "content": "You are a helpful assistant, who is an expert in XMLs & XSLT. " +
             "You respond ONLY in below JSON format, DO NOT ADD ANY OTHER TEXT IN RESPONSE (Do not enclose in tripple ` or add extra words like 'JSON'/'json'). " +
             """
             {
                 "observations": [{"observation": "<observation>"}, {"observation": "<observation>"}]
             }
             Please replace the '<observation>' with your observations in the list of "observations"
             The goal is to answere the "original question".
             """
            },
            {"role": "user", "content": "The generated XSLT, enclosed in triple -. ---" + generated_xslt + "---"},
            {"role": "user", "content": "The prod XSLT, enclosed in triple ~. ~~~" + prod_xslt + "~~~"},
            {"role": "user", "content": "Both the XSLTs, generated XSLT and prod XSLT are to transform the same input XML"},
            {"role": "user", "content": "Original question: What are the difference between these XSLTs?"}
        ]
        compare_agent = setup_agent("GPT4O")
        compare_agent.set_prompts = prompt
        gpt_response = compare_agent.get_chat_completion()
        show_stats(gpt_response)
        LLM_response = gpt_response.choices[0].message.content
        print(f"LLM_response = {LLM_response}")
        has_response, formatted_response = XSLTUtils.consolidate_observations(LLM_response)
        return formatted_response

    @staticmethod
    def copy(generated_xslt):
        return generated_xslt

    @staticmethod
    def get_parameters(uploaded_xslt):
        with open(uploaded_xslt, "r") as f:
            generated_xslt = f.read()
        generated_xslt = generated_xslt.split("\n")
        param_names = []
        parameter_lines = []
        for line in generated_xslt:
            if "xsl:param name" in line:
                split_line = re.split(r"(\"[^\"]*\")",  line)
                parameter_lines.append(split_line)
                param_names.append([split_line[1].split("\"")[1], split_line[3].split("\"")[1]])
        return param_names

    @staticmethod
    def replace_parameters(generated_xslt, new_parameters):
        generated_xslt_split = generated_xslt.split("\n")
        j = 0
        for i, line in enumerate(generated_xslt_split):
            if "xsl:param name" in line:
                new_param = new_parameters.loc[new_parameters.index == j, "Parameter Value"].item()
                split_line = re.split(r"(\"[^\"]*\")",  line)
                split_line[3] = f"\"{new_param}\""
                print(split_line)
                new_line = "".join(split_line)
                generated_xslt_split[i] = new_line
                j += 1
        return "\n".join(generated_xslt_split)

    @staticmethod
    def read_xslt(xslt):
        with open(xslt, "r") as f:
            return f.read()

    @staticmethod
    def diff_texts(text1, text2):
        d = Differ()
        return [
            (token[2:], token[0] if token[0] != " " else None)
            for token in d.compare(text1, text2)
        ]

if __name__ == "__main__":
    # Test the functions
    with open("/Users/nlepakshi/Documents/GitHub/genie/genie_core/config/test_data/ORD_CRE/test/in.xml", "r") as f:
        xml_text = f.read()
    with open("/Users/nlepakshi/Documents/GitHub/genie/genie_core/config/test_data/ORD_CRE/test/ordercreate.xslt", "r") as f:
        xslt_text = f.read()
    output_xml, logs = XSLTUtils.apply_xslt(xslt_text, xml_text, [])
    print(output_xml)