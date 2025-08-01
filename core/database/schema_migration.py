"""
Database Schema Migration for Specification Templates
====================================================

This module handles the migration of the existing database schema to support
specification template storage and management.

New Features:
- specification_templates table for storing template data
- Extended functionality in SQLDatabaseUtils
- Migration rollback capabilities
- Data integrity validation

Usage:
    from core.database.schema_migration import SchemaMigration
    
    migration = SchemaMigration()
    migration.migrate_to_specification_support()
"""

import sqlite3
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SchemaMigration:
    """
    Database schema migration manager for specification template support
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize schema migration
        
        Args:
            db_path: Optional custom database path
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Use default path from project structure
            self.db_path = Path(__file__).parent / "data" / "api_analysis.db"
        
        self.migration_log = []
        logger.info(f"Schema migration initialized for: {self.db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """Create database connection"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=100)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn
    
    def get_current_schema_version(self) -> int:
        """
        Get current schema version
        
        Returns:
            int: Current schema version (0 if no version table exists)
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Check if schema_version table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if not cursor.fetchone():
                # Create schema_version table
                cursor.execute("""
                    CREATE TABLE schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
                cursor.execute("""
                    INSERT INTO schema_version (version, description) 
                    VALUES (0, 'Initial schema')
                """)
                conn.commit()
                version = 0
            else:
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                version = result[0] if result[0] is not None else 0
            
            conn.close()
            logger.info(f"Current schema version: {version}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to get schema version: {e}")
            return 0
    
    def migrate_to_specification_support(self) -> bool:
        """
        Migrate database to support specification templates (version 1)
        
        Returns:
            bool: True if migration successful, False otherwise
        """
        current_version = self.get_current_schema_version()
        
        if current_version >= 1:
            logger.info("Database already supports specification templates")
            return True
        
        logger.info("Starting migration to specification template support...")
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Create specification_templates table
            logger.info("Creating specification_templates table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS specification_templates (
                    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    airline TEXT NOT NULL,
                    section_name TEXT NOT NULL,
                    api_version TEXT,
                    pattern_id INTEGER,
                    specification_content TEXT NOT NULL,
                    mapping_rules TEXT,
                    template_type TEXT DEFAULT 'matched' CHECK (template_type IN ('matched', 'template', 'dummy')),
                    confidence_score REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'manual',
                    requires_manual_review BOOLEAN DEFAULT 0,
                    tags TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES pattern_details(pattern_id),
                    UNIQUE(airline, section_name, api_version, pattern_id)
                )
            """)
            
            # Create indexes for better performance
            logger.info("Creating indexes...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_spec_airline_section 
                ON specification_templates(airline, section_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_spec_template_type 
                ON specification_templates(template_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_spec_requires_review 
                ON specification_templates(requires_manual_review)
            """)
            
            # Create trigger to update updated_date
            logger.info("Creating update trigger...")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_spec_template_timestamp
                AFTER UPDATE ON specification_templates
                FOR EACH ROW
                BEGIN
                    UPDATE specification_templates 
                    SET updated_date = CURRENT_TIMESTAMP 
                    WHERE template_id = NEW.template_id;
                END
            """)
            
            # Update schema version
            cursor.execute("""
                INSERT INTO schema_version (version, description) 
                VALUES (1, 'Added specification templates support')
            """)
            
            conn.commit()
            conn.close()
            
            # Populate with initial data
            self._populate_initial_specification_data()
            
            logger.info("✓ Migration to specification template support completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _populate_initial_specification_data(self) -> bool:
        """
        Populate initial specification template data based on existing patterns
        
        Returns:
            bool: True if population successful, False otherwise
        """
        logger.info("Populating initial specification template data...")
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Get existing pattern mappings
            cursor.execute("""
                SELECT 
                    a.api_name as airline,
                    aps.section_display_name as section_name,
                    COALESCE(av.version_number, 'default') as api_version,
                    pd.pattern_id,
                    pd.pattern_description,
                    pd.pattern_prompt
                FROM api a
                LEFT JOIN apiversion av ON a.api_id = av.api_id
                JOIN api_section aps ON a.api_id = aps.api_id
                JOIN section_pattern_mapping spm ON aps.section_id = spm.section_id AND aps.api_id = spm.api_id
                JOIN pattern_details pd ON spm.pattern_id = pd.pattern_id
                GROUP BY a.api_name, aps.section_display_name, av.version_number, pd.pattern_id
            """)
            
            existing_patterns = cursor.fetchall()
            
            # Create specification templates for existing patterns
            for pattern in existing_patterns:
                airline, section_name, api_version, pattern_id, pattern_desc, pattern_prompt = pattern
                
                # Generate specification content
                spec_content = self._generate_specification_content(
                    airline, section_name, api_version, pattern_desc, pattern_prompt
                )
                
                # Generate mapping rules
                mapping_rules = self._generate_mapping_rules(section_name, pattern_desc)
                
                # Insert specification template
                cursor.execute("""
                    INSERT OR IGNORE INTO specification_templates 
                    (airline, section_name, api_version, pattern_id, specification_content, 
                     mapping_rules, template_type, confidence_score, source, tags)
                    VALUES (?, ?, ?, ?, ?, ?, 'matched', 1.0, 'migration', ?)
                """, (
                    airline,
                    section_name,
                    api_version,
                    pattern_id,
                    spec_content,
                    json.dumps(mapping_rules),
                    json.dumps([airline.lower(), section_name.lower(), "migration"])
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Populated {len(existing_patterns)} specification templates from existing patterns")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate initial data: {e}")
            return False
    
    def _generate_specification_content(
        self, 
        airline: str, 
        section_name: str, 
        api_version: str, 
        pattern_desc: str, 
        pattern_prompt: str
    ) -> str:
        """Generate specification content from pattern data"""
        
        return f"""# {airline} {section_name} Specification

## Overview
Specification for {airline} API {api_version} - {section_name} section.

## Pattern Description
{pattern_desc}

## Validation Rules
Based on pattern: {pattern_prompt}

## Implementation Notes
- Generated from existing pattern data during migration
- Requires review and customization for production use
- Add specific validation rules based on business requirements

## Last Updated
{datetime.now().isoformat()}
"""
    
    def _generate_mapping_rules(self, section_name: str, pattern_desc: str) -> List[Dict[str, Any]]:
        """Generate basic mapping rules from section information"""
        
        return [
            {
                "source_xpath": f"//{section_name}/*",
                "target_field": f"{section_name.lower()}_data",
                "transformation": "identity",
                "validation": "pattern_based",
                "description": pattern_desc,
                "notes": "Generated during migration - customize as needed"
            }
        ]
    
    def rollback_specification_support(self) -> bool:
        """
        Rollback specification template support (downgrade to version 0)
        
        Returns:
            bool: True if rollback successful, False otherwise
        """
        current_version = self.get_current_schema_version()
        
        if current_version < 1:
            logger.info("No specification template support to rollback")
            return True
        
        logger.warning("Rolling back specification template support...")
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Drop specification_templates table and related objects
            cursor.execute("DROP TRIGGER IF EXISTS update_spec_template_timestamp")
            cursor.execute("DROP INDEX IF EXISTS idx_spec_airline_section")
            cursor.execute("DROP INDEX IF EXISTS idx_spec_template_type")
            cursor.execute("DROP INDEX IF EXISTS idx_spec_requires_review")
            cursor.execute("DROP TABLE IF EXISTS specification_templates")
            
            # Update schema version
            cursor.execute("DELETE FROM schema_version WHERE version = 1")
            
            conn.commit()
            conn.close()
            
            logger.info("✓ Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate current database schema
        
        Returns:
            Dict with validation results
        """
        logger.info("Validating database schema...")
        
        validation_results = {
            "schema_version": 0,
            "tables_exist": {},
            "indexes_exist": {},
            "triggers_exist": {},
            "data_integrity": {},
            "errors": []
        }
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Check schema version
            validation_results["schema_version"] = self.get_current_schema_version()
            
            # Check required tables
            required_tables = [
                "api", "apiversion", "api_section", 
                "pattern_details", "section_pattern_mapping"
            ]
            
            if validation_results["schema_version"] >= 1:
                required_tables.append("specification_templates")
            
            for table in required_tables:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                validation_results["tables_exist"][table] = cursor.fetchone() is not None
            
            # Check indexes (for v1+)
            if validation_results["schema_version"] >= 1:
                required_indexes = [
                    "idx_spec_airline_section",
                    "idx_spec_template_type",
                    "idx_spec_requires_review"
                ]
                
                for index in required_indexes:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='index' AND name=?
                    """, (index,))
                    validation_results["indexes_exist"][index] = cursor.fetchone() is not None
            
            # Check triggers (for v1+)
            if validation_results["schema_version"] >= 1:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='trigger' AND name='update_spec_template_timestamp'
                """)
                validation_results["triggers_exist"]["update_spec_template_timestamp"] = cursor.fetchone() is not None
            
            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM api")
            validation_results["data_integrity"]["api_count"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pattern_details")
            validation_results["data_integrity"]["pattern_count"] = cursor.fetchone()[0]
            
            if validation_results["schema_version"] >= 1:
                cursor.execute("SELECT COUNT(*) FROM specification_templates")
                validation_results["data_integrity"]["template_count"] = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info("✓ Schema validation completed")
            
        except Exception as e:
            validation_results["errors"].append(str(e))
            logger.error(f"Schema validation failed: {e}")
        
        return validation_results
    
    def export_schema(self, output_path: Optional[str] = None) -> bool:
        """
        Export current database schema to SQL file
        
        Args:
            output_path: Optional output file path
            
        Returns:
            bool: True if export successful, False otherwise
        """
        if not output_path:
            output_path = f"schema_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        logger.info(f"Exporting schema to: {output_path}")
        
        try:
            conn = self.connect()
            
            with open(output_path, 'w') as f:
                # Export schema
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            
            conn.close()
            
            logger.info(f"✓ Schema exported successfully to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Schema export failed: {e}")
            return False
    
    def get_migration_log(self) -> List[str]:
        """
        Get migration log
        
        Returns:
            List of migration log entries
        """
        return self.migration_log.copy()


# Extended SQLDatabaseUtils with specification template support
class SQLDatabaseUtilsExtended:
    """
    Extended SQLDatabaseUtils with specification template functionality
    """
    
    def __init__(self, db_name="api_analysis.db", base_dir=None):
        """Initialize extended database utils"""
        from core.database.sql_db_utils import SQLDatabaseUtils
        
        # Initialize base class
        self.base_utils = SQLDatabaseUtils(db_name, base_dir)
        
        # Check if schema supports specification templates
        migration = SchemaMigration(str(self.base_utils.db_path))
        self.schema_version = migration.get_current_schema_version()
        
        if self.schema_version < 1:
            logger.warning("Database schema does not support specification templates. Run migration first.")
    
    def get_specification_template(
        self, 
        airline: str, 
        section_name: str, 
        api_version: Optional[str] = None,
        pattern_id: Optional[int] = None
    ) -> Optional[Tuple]:
        """
        Retrieve specification template from database
        
        Args:
            airline: Airline name
            section_name: Section name
            api_version: Optional API version
            pattern_id: Optional pattern ID
            
        Returns:
            Tuple with template data or None if not found
        """
        if self.schema_version < 1:
            logger.error("Specification templates not supported in current schema version")
            return None
        
        query = """
            SELECT template_id, specification_content, mapping_rules, template_type, 
                   confidence_score, source, requires_manual_review, tags, created_date, updated_date
            FROM specification_templates
            WHERE airline = ? AND section_name = ?
        """
        params = [airline, section_name]
        
        if api_version:
            query += " AND api_version = ?"
            params.append(api_version)
        
        if pattern_id:
            query += " AND pattern_id = ?"
            params.append(pattern_id)
        
        query += " ORDER BY confidence_score DESC, created_date DESC LIMIT 1"
        
        return self.base_utils.execute_query(query, params)
    
    def insert_specification_template(
        self,
        airline: str,
        section_name: str,
        specification_content: str,
        api_version: Optional[str] = None,
        pattern_id: Optional[int] = None,
        mapping_rules: Optional[str] = None,
        template_type: str = 'matched',
        confidence_score: float = 1.0,
        source: str = 'manual',
        requires_manual_review: bool = False,
        tags: Optional[str] = None
    ) -> Optional[int]:
        """
        Insert new specification template
        
        Returns:
            Template ID if successful, None otherwise
        """
        if self.schema_version < 1:
            logger.error("Specification templates not supported in current schema version")
            return None
        
        return self.base_utils.insert_data(
            "specification_templates",
            (airline, section_name, api_version, pattern_id, specification_content,
             mapping_rules, template_type, confidence_score, source, requires_manual_review, tags),
            columns=["airline", "section_name", "api_version", "pattern_id", "specification_content",
                    "mapping_rules", "template_type", "confidence_score", "source", "requires_manual_review", "tags"]
        )
    
    def search_specification_templates(
        self,
        airline: Optional[str] = None,
        section_name: Optional[str] = None,
        template_type: Optional[str] = None,
        requires_manual_review: Optional[bool] = None
    ) -> List[Tuple]:
        """
        Search specification templates with filters
        
        Returns:
            List of matching templates
        """
        if self.schema_version < 1:
            logger.error("Specification templates not supported in current schema version")
            return []
        
        query = "SELECT * FROM specification_templates WHERE 1=1"
        params = []
        
        if airline:
            query += " AND airline = ?"
            params.append(airline)
        
        if section_name:
            query += " AND section_name = ?"
            params.append(section_name)
        
        if template_type:
            query += " AND template_type = ?"
            params.append(template_type)
        
        if requires_manual_review is not None:
            query += " AND requires_manual_review = ?"
            params.append(requires_manual_review)
        
        query += " ORDER BY confidence_score DESC, created_date DESC"
        
        return self.base_utils.execute_query(query, params)
    
    def update_specification_template(
        self,
        template_id: int,
        **kwargs
    ) -> bool:
        """
        Update specification template
        
        Args:
            template_id: Template ID to update
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if self.schema_version < 1:
            logger.error("Specification templates not supported in current schema version")
            return False
        
        if not kwargs:
            return True
        
        # Build update query
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE specification_templates SET {set_clause} WHERE template_id = ?"
        params = list(kwargs.values()) + [template_id]
        
        try:
            self.base_utils.execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to update specification template: {e}")
            return False
    
    def delete_specification_template(self, template_id: int) -> bool:
        """
        Delete specification template
        
        Args:
            template_id: Template ID to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if self.schema_version < 1:
            logger.error("Specification templates not supported in current schema version")
            return False
        
        try:
            self.base_utils.execute_query(
                "DELETE FROM specification_templates WHERE template_id = ?",
                [template_id]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete specification template: {e}")
            return False