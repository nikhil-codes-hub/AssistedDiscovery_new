-- Create API table
CREATE TABLE api (
    api_id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create API Version table (missing table that was causing the error)
CREATE TABLE apiversion (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER,
    version_number TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_id) REFERENCES api (api_id)
);

CREATE TABLE api_section (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER NOT NULL,
    section_name TEXT NOT NULL,
    section_display_name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_id) REFERENCES api(api_id)
);


-- Create Pattern Details table
CREATE TABLE pattern_details (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_description TEXT,
    pattern_prompt TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create Section-Pattern Mapping table
CREATE TABLE section_pattern_mapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    api_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES pattern_details(pattern_id),
    FOREIGN KEY (section_id) REFERENCES api_section(section_id),
    FOREIGN KEY (api_id) REFERENCES api(api_id)
);

-- Database schema created without default data
-- Users can add APIs, sections, and patterns as needed per workspace
