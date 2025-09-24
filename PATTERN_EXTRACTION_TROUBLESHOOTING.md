# 🔧 Pattern Extraction Troubleshooting Guide

## Issue: Pattern Extraction Failed

### Error Messages Encountered:
- `⚠️ Pattern Extraction Failed`
- `⚠️ No patterns were extracted.`
- `Could not parse airline-focused pattern extraction response. Using fallback.`

## Root Cause Analysis

The airline-focused pattern extraction is failing due to **JSON parsing issues** with the LLM response. This can happen when:

1. **LLM returns malformed JSON** (common with complex prompts)
2. **Response includes markdown formatting** (```json blocks)
3. **Complex prompt structure** confuses the model
4. **Response length exceeds limits** or gets truncated

## Solutions Implemented

### 1. **Simplified Prompt** (`simplified_airline_focused_extraction.md`)
- ✅ **Cleaner format requirements**
- ✅ **Explicit "NO markdown formatting" instruction**
- ✅ **Simpler JSON structure**
- ✅ **Clear examples**

### 2. **Enhanced Error Handling**
```python
# Better JSON cleaning
if response_cleaned.startswith('```json'):
    response_cleaned = response_cleaned[7:]
    
# Control character removal
cleaned_response = re.sub(r'[\x00-\x1F\x7F]', '', response_cleaned)

# Graceful fallback to standard extraction
```

### 3. **Debug Mode Added**
- 🔧 **Debug Mode** option in UI shows:
  - Selected nodes information
  - XML content length
  - Insights availability
  - Detailed error messages

### 4. **Fallback Strategy**
```
Airline-Focused Prompt → Simplified Prompt → Standard Prompt → Error
```

## Testing Steps

### Step 1: Try Debug Mode
1. Select **🔧 Debug Mode** in Pattern Extraction Mode
2. Click "Extract Patterns"
3. Check debug information in expanded panel
4. Look for specific error messages in logs

### Step 2: Fallback Test
1. If airline-focused fails, system automatically tries **Standard Extraction**
2. Check if standard extraction works (confirms LLM connectivity)
3. If standard works, issue is prompt-specific

### Step 3: Manual Validation
1. Check if selected nodes contain passenger data (PaxList/PassengerList)
2. Verify XML structure is valid
3. Ensure insights are generated properly

## Quick Fixes

### Fix 1: Use Standard Extraction
**Temporary workaround:**
- Select **📊 Standard Extraction** mode
- This uses the proven original prompt
- Will still get pattern filtering benefits

### Fix 2: Simplified Prompts
**Implemented automatically:**
- System now tries simplified prompt first
- Falls back to detailed prompt if needed
- Both are more reliable than original approach

### Fix 3: Check Node Selection
**Common issue:**
- Ensure you've selected relevant XML nodes
- PaxList/PassengerList should be selected
- Don't select too many nodes at once

## Expected Behavior

### ✅ **Working Scenario:**
```
🎯 Pattern Extraction Mode: 🧠 Airline-Focused (Recommended)
→ 🤖 Generating airline-focused patterns with Genie...
→ 🔍 Filtering for airline-specific patterns...
→ 🔍 Filtered out 2 generic patterns, keeping 1 airline-differentiating pattern
→ 🎉 Extraction Complete! Found 1 airline-differentiating patterns (1 high-value)
```

### ❌ **Failing Scenario:**
```
🎯 Pattern Extraction Mode: 🧠 Airline-Focused (Recommended)  
→ 🤖 Generating airline-focused patterns with Genie...
→ ⚠️ Could not parse airline-focused pattern extraction response. Using fallback.
→ 🤖 Generating patterns with Genie... (fallback to standard)
→ 🎉 Extraction Complete! (if fallback works)
```

## Debugging Commands

### Check Log Messages:
- Look for: `"Airline-focused extraction response length"`
- Look for: `"JSON decode error"`
- Look for: `"Problematic response"`

### Verify Prompt Loading:
- Check: `"Airline-focused pattern extraction prompt not found"`
- Verify files exist in `core/config/prompts/generic/`

### Test Standard Extraction:
- If standard works but airline-focused fails = prompt issue
- If both fail = LLM connectivity or XML structure issue

## File Locations

```
core/config/prompts/generic/
├── simplified_airline_focused_extraction.md    ← NEW: Reliable version
├── airline_focused_pattern_extraction.md       ← Detailed version  
└── default_system_prompt_for_pattern_extraction.md ← Standard fallback
```

## Recovery Steps

### Option 1: Use Standard Mode
1. Select **📊 Standard Extraction**
2. Extract patterns normally
3. Review results - still gets airline classification

### Option 2: Debug and Fix  
1. Select **🔧 Debug Mode**
2. Extract patterns
3. Check debug panel for specific errors
4. Report specific error messages for further assistance

### Option 3: Simplify Selection
1. Select fewer XML nodes (focus on PaxList/PassengerList only)
2. Ensure XML is valid and well-formed
3. Try extraction with minimal complexity

The system is now more robust and should work in most scenarios with the fallback mechanisms in place!