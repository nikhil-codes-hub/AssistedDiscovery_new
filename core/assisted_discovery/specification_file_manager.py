"""
Specification File Manager
==========================

This module provides comprehensive functionality for constructing specification files
with mapping retrieval after pattern identification. It integrates with both SQLite
database and Azure AI Search for optimal performance and flexibility.

Features:
- Hybrid approach using SQLite + Azure AI Search
- Intelligent template generation for unmatched patterns
- Comprehensive error handling and logging
- Flexible specification file formats
- Batch processing capabilities

Usage:
    from core.assisted_discovery.specification_file_manager import SpecificationFileManager
    
    spec_manager = SpecificationFileManager()
    specification = spec_manager.construct_specification_file(gap_analysis_result)
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

# Local imports
from core.database.sql_db_utils import SQLDatabaseUtils
from core.database.schema_migration import SQLDatabaseUtilsExtended, SchemaMigration
from core.search.azure_search_manager import AzureSearchManager, SearchResult

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class MappingRule:
    """Structured mapping rule definition"""
    source_xpath: str
    target_field: str
    transformation: str
    validation: str
    description: Optional[str] = None
    notes: Optional[str] = None
    confidence: float = 1.0

@dataclass
class SpecificationDocument:
    """Complete specification document structure"""
    id: str
    airline: str
    api_version: Optional[str]
    section_name: str
    pattern_description: str
    status: str  # 'matched', 'unmatched', 'template'
    specification_content: str
    mapping_rules: List[MappingRule]
    confidence_score: float
    source: str  # 'database', 'azure_search', 'template', 'generated'
    requires_manual_review: bool
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class SpecificationFileManager:
    """
    Comprehensive Specification File Manager
    
    This class orchestrates the construction of specification files by leveraging
    both SQLite database and Azure AI Search for optimal retrieval of mapping
    information for matched and unmatched patterns.
    """
    
    def __init__(self, enable_azure_search: bool = True):
        """
        Initialize Specification File Manager
        
        Args:
            enable_azure_search: Whether to enable Azure AI Search functionality
        """
        # Initialize database utilities
        self.db_utils = SQLDatabaseUtils()
        self.db_utils_extended = SQLDatabaseUtilsExtended()
        
        # Initialize Azure Search (optional)
        self.azure_search = None
        self.enable_azure_search = enable_azure_search
        
        if enable_azure_search:
            try:
                self.azure_search = AzureSearchManager()
                if self.azure_search.test_connection():
                    logger.info("Azure AI Search enabled and connected")
                else:
                    logger.warning("Azure AI Search connection failed - using database only")
                    self.enable_azure_search = False
            except Exception as e:
                logger.warning(f"Azure AI Search initialization failed: {e} - using database only")
                self.enable_azure_search = False
        
        # Ensure database schema is up to date
        self._ensure_schema_compatibility()
        
        logger.info(f"SpecificationFileManager initialized (Azure Search: {self.enable_azure_search})")
    
    def _ensure_schema_compatibility(self):
        """Ensure database schema supports specification templates"""
        migration = SchemaMigration()
        current_version = migration.get_current_schema_version()
        
        if current_version < 1:
            logger.info("Database schema needs migration for specification template support")
            # Note: In production, you might want to prompt user or auto-migrate
            # For now, we'll log a warning
            logger.warning("Please run schema migration to enable full specification template functionality")
    
    def construct_specification_file(self, gap_analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to construct specification file after pattern identification
        
        Args:
            gap_analysis_result: Result from PatternIdentifyManager.verify_and_confirm_airline()
            
        Returns:
            Complete specification file with mappings and metadata
        """
        logger.info("Starting specification file construction...")
        
        try:
            specifications = []
            processing_stats = {
                "total_sections": 0,
                "total_rules": 0,
                "matched_rules": 0,
                "unmatched_rules": 0,
                "template_generated": 0,
                "database_retrieved": 0,
                "azure_search_retrieved": 0,
                "dummy_generated": 0
            }
            
            # Process each section
            for section in gap_analysis_result.get('sections', []):
                processing_stats["total_sections"] += 1
                section_specs = self._process_section(section, processing_stats)
                specifications.extend(section_specs)
            
            # Compile final specification
            final_specification = self._compile_final_specification(
                specifications, 
                gap_analysis_result.get('matched_airlines', []),
                processing_stats
            )
            
            logger.info(f"Specification file construction completed. Generated {len(specifications)} specifications.")
            return final_specification
            
        except Exception as e:
            logger.error(f"Specification file construction failed: {e}")
            return self._create_error_specification(str(e))
    
    def _process_section(self, section: Dict[str, Any], stats: Dict[str, int]) -> List[SpecificationDocument]:
        """
        Process individual section and its rules
        
        Args:
            section: Section data from gap analysis
            stats: Processing statistics dictionary
            
        Returns:
            List of SpecificationDocument objects
        """
        section_specifications = []
        section_name = section.get('sectionName', 'unknown')
        
        logger.info(f"Processing section: {section_name}")
        
        for rule in section.get('rules', []):
            stats["total_rules"] += 1
            
            try:
                if rule.get('matched', False):
                    stats["matched_rules"] += 1
                    spec = self._get_matched_specification(section, rule, stats)
                else:
                    stats["unmatched_rules"] += 1
                    spec = self._create_unmatched_specification(section, rule, stats)
                
                if spec:
                    section_specifications.append(spec)
                
            except Exception as e:
                logger.error(f"Failed to process rule for {section_name}: {e}")
                # Create error specification
                error_spec = self._create_error_specification_document(section, rule, str(e))
                section_specifications.append(error_spec)
        
        return section_specifications
    
    def _get_matched_specification(
        self, 
        section: Dict[str, Any], 
        rule: Dict[str, Any], 
        stats: Dict[str, int]
    ) -> Optional[SpecificationDocument]:
        """
        Retrieve specification for matched patterns using hybrid approach
        
        Args:
            section: Section data
            rule: Rule data
            stats: Processing statistics
            
        Returns:
            SpecificationDocument or None if retrieval fails
        """
        airline = rule.get('airline', 'unknown')
        section_name = section.get('sectionName', 'unknown')
        api_version = rule.get('apiVersion', 'default')
        
        logger.info(f"Retrieving matched specification: {airline}/{section_name}/{api_version}")
        
        # Strategy 1: Try database first for exact matches
        db_spec = self._get_database_specification(airline, section_name, api_version)
        if db_spec:
            stats["database_retrieved"] += 1
            return self._create_specification_from_database(db_spec, section, rule)
        
        # Strategy 2: Try Azure AI Search for semantic matches
        if self.enable_azure_search:
            search_spec = self._get_azure_search_specification(airline, section_name, rule)
            if search_spec:
                stats["azure_search_retrieved"] += 1
                return self._create_specification_from_search(search_spec, section, rule)
        
        # Strategy 3: Generate from pattern details as fallback
        pattern_spec = self._create_specification_from_pattern(section, rule)
        if pattern_spec:
            stats["template_generated"] += 1
        
        return pattern_spec
    
    def _get_database_specification(
        self, 
        airline: str, 
        section_name: str, 
        api_version: str
    ) -> Optional[Tuple]:
        """
        Retrieve specification from database
        
        Returns:
            Database result tuple or None
        """
        try:
            # Try extended database utils first (if schema supports it)
            if self.db_utils_extended.schema_version >= 1:
                result = self.db_utils_extended.get_specification_template(
                    airline=airline,
                    section_name=section_name,
                    api_version=api_version
                )
                if result and len(result) > 0:
                    return result[0]
            
            # Fallback to pattern mapping query
            query = """
                SELECT a.api_name, COALESCE(av.version_number, 'N/A') as api_version, 
                       pd.pattern_description, pd.pattern_prompt, aps.section_display_name
                FROM api a
                LEFT JOIN apiversion av ON a.api_id = av.api_id
                JOIN api_section aps ON a.api_id = aps.api_id
                JOIN section_pattern_mapping spm ON aps.section_id = spm.section_id AND aps.api_id = spm.api_id
                JOIN pattern_details pd ON spm.pattern_id = pd.pattern_id
                WHERE a.api_name = ? AND aps.section_display_name = ?
                ORDER BY pd.pattern_id LIMIT 1
            """
            
            result = self.db_utils.execute_query(query, (airline, section_name))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Database specification retrieval failed: {e}")
            return None
    
    def _get_azure_search_specification(
        self, 
        airline: str, 
        section_name: str, 
        rule: Dict[str, Any]
    ) -> Optional[SearchResult]:
        """
        Retrieve specification from Azure AI Search
        
        Returns:
            SearchResult or None
        """
        try:
            # Build search query
            search_query = f"{airline} {section_name} {rule.get('verificationRule', '')}"
            filters = f"airline eq '{airline}' and template_type eq 'matched'"
            
            # Perform semantic search
            results = self.azure_search.semantic_search(
                query=search_query,
                filters=filters,
                top=1
            )
            
            if results and len(results) > 0 and results[0].search_score >= 0.7:
                return results[0]
            
            # Fallback to regular search if semantic search doesn't find good matches
            results = self.azure_search.search_specifications(
                query=search_query,
                filters=filters,
                top=1
            )
            
            if results and len(results) > 0 and results[0].search_score >= 0.5:
                return results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Azure Search specification retrieval failed: {e}")
            return None
    
    def _create_unmatched_specification(
        self, 
        section: Dict[str, Any], 
        rule: Dict[str, Any], 
        stats: Dict[str, int]
    ) -> Optional[SpecificationDocument]:
        """
        Create specification for unmatched patterns
        
        Args:
            section: Section data
            rule: Rule data
            stats: Processing statistics
            
        Returns:
            SpecificationDocument for unmatched pattern
        """
        airline = rule.get('airline', 'unknown')
        section_name = section.get('sectionName', 'unknown')
        
        logger.info(f"Creating unmatched specification: {airline}/{section_name}")
        
        # Strategy 1: Find similar patterns using Azure AI Search
        if self.enable_azure_search:
            similar_spec = self._find_similar_specification_template(section_name, airline)
            if similar_spec:
                stats["template_generated"] += 1
                return self._create_specification_from_template(similar_spec, section, rule)
        
        # Strategy 2: Generate dummy specification
        stats["dummy_generated"] += 1
        return self._generate_dummy_specification(section, rule)
    
    def _find_similar_specification_template(
        self, 
        section_name: str, 
        airline: Optional[str] = None
    ) -> Optional[SearchResult]:
        """
        Find similar specification templates using Azure AI Search
        
        Returns:
            SearchResult for similar template or None
        """
        try:
            # Use vector search or semantic search to find similar patterns
            similar_specs = self.azure_search.find_similar_specifications(
                section_name=section_name,
                airline=airline,
                similarity_threshold=0.6,
                top=1
            )
            
            return similar_specs[0] if similar_specs else None
            
        except Exception as e:
            logger.error(f"Failed to find similar specification template: {e}")
            return None
    
    def _create_specification_from_database(
        self, 
        db_result: Tuple, 
        section: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> SpecificationDocument:
        """Create SpecificationDocument from database result"""
        
        # Handle both extended and legacy database formats
        if len(db_result) >= 10:  # Extended format
            (template_id, spec_content, mapping_rules, template_type, 
             confidence_score, source, requires_manual_review, tags, created_date, updated_date) = db_result[:10]
            
            # Parse mapping rules
            try:
                mapping_rules_list = json.loads(mapping_rules) if mapping_rules else []
            except json.JSONDecodeError:
                mapping_rules_list = []
            
        else:  # Legacy format
            api_name, api_version, pattern_description, pattern_prompt, section_display_name = db_result
            spec_content = self._generate_specification_content_from_pattern(
                api_name, section_display_name, api_version, pattern_description, pattern_prompt
            )
            mapping_rules_list = self._generate_mapping_rules_from_pattern(section_display_name, pattern_description)
            confidence_score = 0.8
            source = "database_legacy"
            requires_manual_review = True
        
        # Convert mapping rules to MappingRule objects
        mapping_objects = []
        for rule_data in mapping_rules_list:
            if isinstance(rule_data, dict):
                mapping_objects.append(MappingRule(
                    source_xpath=rule_data.get('source_xpath', ''),
                    target_field=rule_data.get('target_field', ''),
                    transformation=rule_data.get('transformation', 'identity'),
                    validation=rule_data.get('validation', 'none'),
                    description=rule_data.get('description', ''),
                    notes=rule_data.get('notes', ''),
                    confidence=rule_data.get('confidence', 1.0)
                ))
        
        return SpecificationDocument(
            id=f"{rule['airline']}_{section['sectionName']}_{rule.get('apiVersion', 'default')}_{uuid.uuid4().hex[:8]}",
            airline=rule['airline'],
            api_version=rule.get('apiVersion'),
            section_name=section['sectionName'],
            pattern_description=rule.get('verificationRule', 'Database specification'),
            status='matched',
            specification_content=spec_content,
            mapping_rules=mapping_objects,
            confidence_score=confidence_score,
            source=source,
            requires_manual_review=requires_manual_review,
            metadata={
                "retrieval_method": "database",
                "pattern_matched": True,
                "verification_rule": rule.get('verificationRule', ''),
                "match_reason": rule.get('reason', '')
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _create_specification_from_search(
        self, 
        search_result: SearchResult, 
        section: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> SpecificationDocument:
        """Create SpecificationDocument from Azure Search result"""
        
        # Convert mapping rules to MappingRule objects
        mapping_objects = []
        for rule_data in search_result.mapping_rules:
            if isinstance(rule_data, dict):
                mapping_objects.append(MappingRule(
                    source_xpath=rule_data.get('source_xpath', ''),
                    target_field=rule_data.get('target_field', ''),
                    transformation=rule_data.get('transformation', 'identity'),
                    validation=rule_data.get('validation', 'none'),
                    description=rule_data.get('description', ''),
                    notes=rule_data.get('notes', ''),
                    confidence=rule_data.get('confidence', search_result.search_score)
                ))
        
        return SpecificationDocument(
            id=f"{rule['airline']}_{section['sectionName']}_{rule.get('apiVersion', 'default')}_{uuid.uuid4().hex[:8]}",
            airline=rule['airline'],
            api_version=rule.get('apiVersion'),
            section_name=section['sectionName'],
            pattern_description=rule.get('verificationRule', search_result.specification_content[:100]),
            status='matched',
            specification_content=search_result.specification_content,
            mapping_rules=mapping_objects,
            confidence_score=search_result.search_score,
            source='azure_search',
            requires_manual_review=search_result.requires_manual_review,
            metadata={
                "retrieval_method": "azure_search",
                "pattern_matched": True,
                "search_score": search_result.search_score,
                "original_id": search_result.id,
                "verification_rule": rule.get('verificationRule', ''),
                "match_reason": rule.get('reason', '')
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _create_specification_from_pattern(
        self, 
        section: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> SpecificationDocument:
        """Create SpecificationDocument from pattern details"""
        
        spec_content = self._generate_specification_content_from_pattern(
            rule['airline'],
            section['sectionName'],
            rule.get('apiVersion', 'default'),
            rule.get('verificationRule', 'Pattern-based specification'),
            rule.get('reason', 'Generated from pattern analysis')
        )
        
        mapping_rules = self._generate_mapping_rules_from_pattern(
            section['sectionName'],
            rule.get('verificationRule', 'Pattern-based mapping')
        )
        
        mapping_objects = [MappingRule(**rule_data) for rule_data in mapping_rules]
        
        return SpecificationDocument(
            id=f"{rule['airline']}_{section['sectionName']}_{rule.get('apiVersion', 'default')}_pattern_{uuid.uuid4().hex[:8]}",
            airline=rule['airline'],
            api_version=rule.get('apiVersion'),
            section_name=section['sectionName'],
            pattern_description=rule.get('verificationRule', 'Pattern-based specification'),
            status='matched',
            specification_content=spec_content,
            mapping_rules=mapping_objects,
            confidence_score=0.7,
            source='pattern_generated',
            requires_manual_review=True,
            metadata={
                "retrieval_method": "pattern_generation",
                "pattern_matched": True,
                "verification_rule": rule.get('verificationRule', ''),
                "match_reason": rule.get('reason', '')
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _create_specification_from_template(
        self, 
        template: SearchResult, 
        section: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> SpecificationDocument:
        """Create SpecificationDocument from similar template"""
        
        # Customize template content for this specific case
        customized_content = self._customize_template_content(
            template.specification_content,
            rule['airline'],
            section['sectionName'],
            rule.get('apiVersion', 'default')
        )
        
        # Adapt mapping rules
        adapted_rules = self._adapt_mapping_rules(template.mapping_rules, section['sectionName'])
        mapping_objects = [MappingRule(**rule_data) for rule_data in adapted_rules]
        
        return SpecificationDocument(
            id=f"{rule['airline']}_{section['sectionName']}_{rule.get('apiVersion', 'default')}_template_{uuid.uuid4().hex[:8]}",
            airline=rule['airline'],
            api_version=rule.get('apiVersion'),
            section_name=section['sectionName'],
            pattern_description=f"Template-based specification (similar to {template.airline} {template.section_name})",
            status='unmatched',
            specification_content=customized_content,
            mapping_rules=mapping_objects,
            confidence_score=template.search_score * 0.8,  # Reduce confidence for template-based
            source='template_adapted',
            requires_manual_review=True,
            metadata={
                "retrieval_method": "template_adaptation",
                "pattern_matched": False,
                "template_source": template.id,
                "template_airline": template.airline,
                "template_section": template.section_name,
                "verification_rule": rule.get('verificationRule', ''),
                "match_reason": rule.get('reason', '')
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _generate_dummy_specification(
        self, 
        section: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> SpecificationDocument:
        """Generate dummy specification for completely unmatched patterns"""
        
        spec_content = self._create_dummy_specification_content(section, rule)
        mapping_rules = self._create_dummy_mapping_rules(section['sectionName'])
        mapping_objects = [MappingRule(**rule_data) for rule_data in mapping_rules]
        
        return SpecificationDocument(
            id=f"{rule['airline']}_{section['sectionName']}_dummy_{uuid.uuid4().hex[:8]}",
            airline=rule['airline'],
            api_version=rule.get('apiVersion'),
            section_name=section['sectionName'],
            pattern_description=rule.get('verificationRule', 'No verification rule available'),
            status='unmatched',
            specification_content=spec_content,
            mapping_rules=mapping_objects,
            confidence_score=0.0,
            source='generated_dummy',
            requires_manual_review=True,
            metadata={
                "retrieval_method": "dummy_generation",
                "pattern_matched": False,
                "verification_rule": rule.get('verificationRule', ''),
                "match_reason": rule.get('reason', ''),
                "warning": "This is a dummy specification requiring manual configuration"
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _generate_specification_content_from_pattern(
        self, 
        airline: str, 
        section_name: str, 
        api_version: str, 
        pattern_description: str, 
        pattern_prompt: str
    ) -> str:
        """Generate specification content from pattern data"""
        
        return f"""# {airline} {section_name} Specification

## Overview
Specification for {airline} API {api_version} - {section_name} section.

## Pattern Description
{pattern_description}

## Verification Rules
{pattern_prompt}

## Implementation Notes
- Generated from pattern analysis during specification file construction
- Requires review and customization for production use
- Add specific validation rules based on business requirements
- Test with sample XML data before deployment

## Validation Requirements
1. Verify XML structure matches expected pattern
2. Validate data types and constraints
3. Check business rule compliance
4. Ensure proper error handling

## Last Generated
{datetime.now().isoformat()}

## Next Steps
1. Review and customize mapping rules
2. Add business-specific validation logic
3. Test with sample data
4. Update confidence scores based on testing results
"""
    
    def _generate_mapping_rules_from_pattern(
        self, 
        section_name: str, 
        pattern_description: str
    ) -> List[Dict[str, Any]]:
        """Generate mapping rules from pattern information"""
        
        return [
            {
                "source_xpath": f"//{section_name}/*",
                "target_field": f"{section_name.lower()}_data",
                "transformation": "identity",
                "validation": "pattern_based",
                "description": pattern_description,
                "notes": "Generated from pattern analysis - customize as needed",
                "confidence": 0.7
            },
            {
                "source_xpath": f"//{section_name}/@*",
                "target_field": f"{section_name.lower()}_attributes",
                "transformation": "attribute_extract",
                "validation": "optional",
                "description": f"Extract attributes from {section_name} element",
                "notes": "Consider which attributes are actually needed",
                "confidence": 0.5
            }
        ]
    
    def _create_dummy_specification_content(
        self, 
        section: Dict[str, Any], 
        rule: Dict[str, Any]
    ) -> str:
        """Create dummy specification content"""
        
        section_name = section.get('sectionName', 'unknown')
        airline = rule.get('airline', 'unknown')
        api_version = rule.get('apiVersion', 'unknown')
        
        return f"""# DUMMY: {airline} {section_name} Specification

## ⚠️ WARNING: This is a dummy specification
This specification was auto-generated for an unmatched pattern and requires manual configuration.

## Pattern Details
- **Airline**: {airline}
- **API Version**: {api_version}
- **Section**: {section_name}
- **Verification Rule**: {rule.get('verificationRule', 'Not specified')}
- **Match Status**: Unmatched
- **Reason**: {rule.get('reason', 'Pattern not found in database or templates')}

## Required Actions
1. **Identify Section Purpose**: Determine what this XML section contains and its business purpose
2. **Define Mapping Rules**: Create proper XPath mappings to target fields
3. **Add Validation Logic**: Implement business rules and data validation
4. **Test Implementation**: Validate with sample XML data
5. **Update Confidence**: Adjust confidence scores based on testing

## Placeholder Mapping Rules
The mapping rules below are placeholders and need to be customized:

```xml
<!-- Example XML structure (replace with actual) -->
<{section_name}>
  <!-- Add expected child elements here -->
</{section_name}>
```

## Business Rules
- [ ] Define required fields
- [ ] Set up data type validations  
- [ ] Implement business logic constraints
- [ ] Add error handling procedures

## Testing Checklist
- [ ] Unit test mapping rules
- [ ] Integration test with sample data
- [ ] Performance test with large datasets
- [ ] Error handling verification

---
**Generated**: {datetime.now().isoformat()}
**Status**: Requires immediate manual review and configuration
"""
    
    def _create_dummy_mapping_rules(self, section_name: str) -> List[Dict[str, Any]]:
        """Create dummy mapping rules"""
        
        return [
            {
                "source_xpath": f"//{section_name}/*",
                "target_field": f"{section_name.lower()}_content",
                "transformation": "identity",
                "validation": "none",
                "description": "Placeholder mapping for all child elements",
                "notes": "REQUIRES MANUAL CONFIGURATION - Replace with specific field mappings",
                "confidence": 0.0
            },
            {
                "source_xpath": f"//{section_name}/text()",
                "target_field": f"{section_name.lower()}_text",
                "transformation": "text_extract",
                "validation": "optional",
                "description": "Extract text content if any",
                "notes": "May not be needed depending on XML structure",
                "confidence": 0.0
            }
        ]
    
    def _customize_template_content(
        self, 
        template_content: str, 
        airline: str, 
        section_name: str, 
        api_version: str
    ) -> str:
        """Customize template content for specific airline/section"""
        
        # Simple template customization - replace placeholders
        customized = template_content
        
        # Add customization header
        header = f"""# {airline} {section_name} Specification (Template-Based)

## 📋 Note: This specification was adapted from a similar template
Original template has been customized for {airline} {section_name} v{api_version}.
Please review and modify as needed for your specific requirements.

---

"""
        
        return header + customized
    
    def _adapt_mapping_rules(
        self, 
        template_rules: List[Dict[str, Any]], 
        target_section: str
    ) -> List[Dict[str, Any]]:
        """Adapt mapping rules from template to target section"""
        
        adapted_rules = []
        
        for rule in template_rules:
            adapted_rule = rule.copy()
            
            # Update XPath to use target section
            if 'source_xpath' in adapted_rule:
                # Simple section name replacement
                adapted_rule['source_xpath'] = adapted_rule['source_xpath'].replace(
                    rule.get('source_xpath', '').split('/')[-1] if '//' in rule.get('source_xpath', '') else '',
                    target_section
                )
            
            # Update target field name
            if 'target_field' in adapted_rule:
                adapted_rule['target_field'] = f"{target_section.lower()}_{adapted_rule['target_field']}"
            
            # Reduce confidence for adapted rules
            adapted_rule['confidence'] = adapted_rule.get('confidence', 1.0) * 0.6
            
            # Add note about adaptation
            adapted_rule['notes'] = f"Adapted from template. {adapted_rule.get('notes', '')}".strip()
            
            adapted_rules.append(adapted_rule)
        
        return adapted_rules
    
    def _create_error_specification_document(
        self, 
        section: Dict[str, Any], 
        rule: Dict[str, Any], 
        error: str
    ) -> SpecificationDocument:
        """Create error specification document when processing fails"""
        
        return SpecificationDocument(
            id=f"error_{rule.get('airline', 'unknown')}_{section.get('sectionName', 'unknown')}_{uuid.uuid4().hex[:8]}",
            airline=rule.get('airline', 'unknown'),
            api_version=rule.get('apiVersion'),
            section_name=section.get('sectionName', 'unknown'),
            pattern_description=f"ERROR: {error}",
            status='error',
            specification_content=f"# ERROR IN SPECIFICATION GENERATION\n\nAn error occurred while generating specification:\n{error}",
            mapping_rules=[],
            confidence_score=0.0,
            source='error',
            requires_manual_review=True,
            metadata={
                "error": error,
                "verification_rule": rule.get('verificationRule', ''),
                "match_reason": rule.get('reason', '')
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _compile_final_specification(
        self, 
        specifications: List[SpecificationDocument], 
        matched_airlines: List[str],
        processing_stats: Dict[str, int]
    ) -> Dict[str, Any]:
        """Compile final specification file with metadata and organization"""
        
        # Categorize specifications
        matched_specs = [spec for spec in specifications if spec.status == 'matched']
        unmatched_specs = [spec for spec in specifications if spec.status == 'unmatched']
        error_specs = [spec for spec in specifications if spec.status == 'error']
        
        # Calculate confidence statistics
        all_scores = [spec.confidence_score for spec in specifications if spec.confidence_score > 0]
        confidence_stats = {
            "average": sum(all_scores) / len(all_scores) if all_scores else 0,
            "high_confidence": len([s for s in all_scores if s >= 0.8]),
            "medium_confidence": len([s for s in all_scores if 0.5 <= s < 0.8]),
            "low_confidence": len([s for s in all_scores if 0 < s < 0.5])
        }
        
        # Create manual review list
        manual_review_required = [
            {
                "id": spec.id,
                "airline": spec.airline,
                "section_name": spec.section_name,
                "reason": "requires_manual_review",
                "confidence_score": spec.confidence_score,
                "priority": "high" if spec.confidence_score == 0 else "medium"
            }
            for spec in specifications 
            if spec.requires_manual_review
        ]
        
        # Convert specifications to dictionaries for JSON serialization
        spec_dicts = [self._specification_to_dict(spec) for spec in specifications]
        matched_dicts = [self._specification_to_dict(spec) for spec in matched_specs]
        unmatched_dicts = [self._specification_to_dict(spec) for spec in unmatched_specs]
        error_dicts = [self._specification_to_dict(spec) for spec in error_specs]
        
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "SpecificationFileManager",
                "version": "1.0",
                "total_specifications": len(specifications),
                "matched_count": len(matched_specs),
                "unmatched_count": len(unmatched_specs),
                "error_count": len(error_specs),
                "matched_airlines": list(matched_airlines),
                "processing_statistics": processing_stats,
                "confidence_summary": confidence_stats,
                "azure_search_enabled": self.enable_azure_search
            },
            "specifications": {
                "all": spec_dicts,
                "matched": matched_dicts,
                "unmatched": unmatched_dicts,
                "errors": error_dicts
            },
            "manual_review_required": manual_review_required,
            "summary": {
                "total_rules_processed": processing_stats["total_rules"],
                "successful_mappings": len(specifications) - len(error_specs),
                "retrieval_methods_used": {
                    "database": processing_stats["database_retrieved"],
                    "azure_search": processing_stats["azure_search_retrieved"],
                    "template_generation": processing_stats["template_generated"],
                    "dummy_generation": processing_stats["dummy_generated"]
                },
                "quality_indicators": {
                    "high_confidence_specs": confidence_stats["high_confidence"],
                    "requires_review_count": len(manual_review_required),
                    "error_rate": len(error_specs) / len(specifications) if specifications else 0
                }
            }
        }
    
    def _specification_to_dict(self, spec: SpecificationDocument) -> Dict[str, Any]:
        """Convert SpecificationDocument to dictionary for JSON serialization"""
        
        spec_dict = asdict(spec)
        
        # Convert MappingRule objects to dictionaries
        spec_dict['mapping_rules'] = [asdict(rule) for rule in spec.mapping_rules]
        
        return spec_dict
    
    def _create_error_specification(self, error: str) -> Dict[str, Any]:
        """Create error specification when entire process fails"""
        
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "SpecificationFileManager",
                "version": "1.0",
                "status": "error",
                "error": error
            },
            "specifications": {
                "all": [],
                "matched": [],
                "unmatched": [],
                "errors": []
            },
            "manual_review_required": [],
            "summary": {
                "total_rules_processed": 0,
                "successful_mappings": 0,
                "error_message": f"Specification file generation failed: {error}"
            }
        }
    
    def save_specification_to_file(self, specification: Dict[str, Any], file_path: str) -> bool:
        """
        Save specification to JSON file
        
        Args:
            specification: Specification dictionary
            file_path: Output file path
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(specification, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Specification saved to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save specification to file: {e}")
            return False
    
    def load_specification_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load specification from JSON file
        
        Args:
            file_path: Input file path
            
        Returns:
            Specification dictionary or None if load failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                specification = json.load(f)
            
            logger.info(f"Specification loaded from: {file_path}")
            return specification
            
        except Exception as e:
            logger.error(f"Failed to load specification from file: {e}")
            return None