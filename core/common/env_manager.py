"""
Environment Variable Manager for GENIe Application
Handles loading and saving .env file parameters
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from core.common.logging_manager import get_logger, log_user_action, log_error

logger = get_logger(__name__)

@dataclass
class EnvVariable:
    """Represents an environment variable with metadata"""
    key: str
    value: str
    comment: str = ""
    is_commented: bool = False
    group: str = "General"

class EnvManager:
    """Manages environment variables from .env file"""
    
    def __init__(self, env_file_path: Optional[str] = None):
        """
        Initialize EnvManager
        
        Args:
            env_file_path: Path to .env file. If None, looks for .env in project root.
        """
        if env_file_path is None:
            # Look for .env in project root
            project_root = Path(__file__).parent.parent.parent
            self.env_file_path = project_root / ".env"
        else:
            self.env_file_path = Path(env_file_path)
        
        logger.info(f"EnvManager initialized with file: {self.env_file_path}")
        
        # Environment variable groups for organization
        self.groups = {
            "GPT-4O Azure": ["GPT4O_AZURE_OPENAI_KEY", "GPT4O_AZURE_OPENAI_ENDPOINT", "GPT4O_AZURE_API_VERSION", "GPT4O_MODEL_DEPLOYMENT_NAME"],
            "GPT-4 Turbo Azure": ["GPT4Turbo_AZURE_OPENAI_KEY", "GPT4Turbo_AZURE_OPENAI_ENDPOINT", "GPT4Turbo_AZURE_API_VERSION", "GPT4Turbo_MODEL_DEPLOYMENT_NAME"],
            "GPT-4 32K Azure": ["GPT4_32K_AZURE_OPENAI_KEY", "GPT4_32K_AZURE_OPENAI_ENDPOINT", "GPT4_32K_AZURE_API_VERSION", "GPT4_32K_MODEL_DEPLOYMENT_NAME"],
            "O1 Azure": ["o1_AZURE_OPENAI_KEY", "o1_AZURE_OPENAI_ENDPOINT", "o1_AZURE_API_VERSION", "o1_MODEL_DEPLOYMENT_NAME"],
            "O3 Mini Azure": ["o3_mini_AZURE_OPENAI_KEY", "o3_mini_AZURE_OPENAI_ENDPOINT", "o3_mini_AZURE_API_VERSION", "o3_mini_MODEL_DEPLOYMENT_NAME"],
            "Text Embedding": ["ADA_EMBD_AZURE_OPENAI_KEY", "ADA_EMBD_AZURE_OPENAI_ENDPOINT", "ADA_EMBD_AZURE_API_VERSION", "ADA_EMBD_MODEL_DEPLOYMENT_NAME"],
            "ChromaDB": ["ALLOW_RESET"],
            "Atlassian": ["ATLASSIAN_BOT_USERNAME", "ATLASSIAN_BOT_SECRET"]
        }
    
    def load_env_variables(self) -> Dict[str, EnvVariable]:
        """
        Load environment variables from .env file
        
        Returns:
            Dictionary mapping variable names to EnvVariable objects
        """
        variables = {}
        
        if not self.env_file_path.exists():
            logger.warning(f".env file not found at: {self.env_file_path}")
            return variables
        
        try:
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_comment = ""
            
            for line_num, line in enumerate(lines, 1):
                line = line.rstrip('\n\r')
                
                # Skip empty lines
                if not line.strip():
                    current_comment = ""
                    continue
                
                # Handle comments
                if line.strip().startswith('#'):
                    current_comment = line.strip()
                    continue
                
                # Handle commented environment variables (lines starting with # followed by variable)
                commented_match = re.match(r'^#\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
                if commented_match:
                    key, value = commented_match.groups()
                    value = value.strip().strip('"\'')
                    
                    variables[key] = EnvVariable(
                        key=key,
                        value=value,
                        comment=current_comment,
                        is_commented=True,
                        group=self._get_variable_group(key)
                    )
                    current_comment = ""
                    continue
                
                # Handle active environment variables
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    variables[key] = EnvVariable(
                        key=key,
                        value=value,
                        comment=current_comment,
                        is_commented=False,
                        group=self._get_variable_group(key)
                    )
                    current_comment = ""
            
            logger.info(f"Loaded {len(variables)} environment variables from .env file")
            return variables
            
        except Exception as e:
            log_error(f"Failed to load .env file: {str(e)}")
            return variables
    
    def save_env_variables(self, variables: Dict[str, EnvVariable]) -> bool:
        """
        Save environment variables to .env file
        
        Args:
            variables: Dictionary of EnvVariable objects to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Group variables by their groups for organized output
            grouped_vars = {}
            ungrouped_vars = []
            
            for var in variables.values():
                if var.group != "General":
                    if var.group not in grouped_vars:
                        grouped_vars[var.group] = []
                    grouped_vars[var.group].append(var)
                else:
                    ungrouped_vars.append(var)
            
            # Generate .env file content
            lines = []
            
            # Add ungrouped variables first
            for var in ungrouped_vars:
                if var.comment:
                    lines.append(var.comment)
                
                if var.is_commented:
                    lines.append(f"# {var.key}=\"{var.value}\"")
                else:
                    lines.append(f"{var.key}=\"{var.value}\"")
                lines.append("")  # Empty line after each variable
            
            # Add grouped variables
            for group_name, group_vars in grouped_vars.items():
                if group_vars:
                    # Add group header comment
                    lines.append(f"#{group_name}")
                    lines.append("#" * (len(group_name) + 20))
                    
                    for var in group_vars:
                        if var.comment and var.comment != f"#{group_name}":
                            lines.append(var.comment)
                        
                        if var.is_commented:
                            lines.append(f"# {var.key}=\"{var.value}\"")
                        else:
                            lines.append(f"{var.key}=\"{var.value}\"")
                    
                    lines.append("#" * 24)
                    lines.append("")  # Empty line after each group
            
            # Write to file
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            logger.info(f"Successfully saved {len(variables)} environment variables to .env file")
            log_user_action("Updated .env file configuration")
            return True
            
        except Exception as e:
            log_error(f"Failed to save .env file: {str(e)}")
            return False
    
    def _get_variable_group(self, variable_name: str) -> str:
        """
        Get the group for a variable name
        
        Args:
            variable_name: Name of the environment variable
            
        Returns:
            Group name or "General" if not found
        """
        for group_name, variables in self.groups.items():
            if variable_name in variables:
                return group_name
        return "General"
    
    def get_variables_by_group(self, variables: Dict[str, EnvVariable]) -> Dict[str, List[EnvVariable]]:
        """
        Group variables by their categories
        
        Args:
            variables: Dictionary of EnvVariable objects
            
        Returns:
            Dictionary mapping group names to lists of variables
        """
        grouped = {}
        
        for var in variables.values():
            group = var.group
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(var)
        
        # Sort variables within each group
        for group in grouped.values():
            group.sort(key=lambda x: x.key)
        
        return grouped
    
    def validate_variable(self, key: str, value: str) -> Tuple[bool, str]:
        """
        Validate an environment variable
        
        Args:
            key: Variable name
            value: Variable value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation rules
        if not key:
            return False, "Variable name cannot be empty"
        
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
            return False, "Variable name must contain only letters, numbers, and underscores"
        
        # Specific validations for known variables
        if "ENDPOINT" in key and value:
            if not value.startswith(('http://', 'https://')):
                return False, "Endpoint must be a valid URL starting with http:// or https://"
        
        if "API_VERSION" in key and value:
            if not re.match(r'^\d{4}-\d{2}-\d{2}(-preview)?$', value):
                return False, "API version should be in format YYYY-MM-DD or YYYY-MM-DD-preview"
        
        if "KEY" in key and value:
            if len(value) < 10:
                return False, "API keys should be at least 10 characters long"
        
        return True, ""
    
    def backup_env_file(self) -> bool:
        """
        Create a backup of the current .env file
        
        Returns:
            bool: True if backup was created successfully
        """
        if not self.env_file_path.exists():
            return False
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.env_file_path.parent / f".env.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.env_file_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            log_error(f"Failed to create backup: {str(e)}")
            return False