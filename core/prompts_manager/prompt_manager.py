from abc import ABC, abstractmethod

class promptManager:
    def __init__(self):
        self.prompts = {}

    def add_prompt(self, name, prompt):
        self.prompts[name] = prompt

    def get_prompt(self, name):
        return self.prompts.get(name, "Prompt not found.")
    
    @abstractmethod
    def get_default_system_prompt(self):
        pass
    
    @abstractmethod
    def load_default_prompts(self, params):
        pass
    
    @abstractmethod
    def load_prompts(self, params):
        pass
    