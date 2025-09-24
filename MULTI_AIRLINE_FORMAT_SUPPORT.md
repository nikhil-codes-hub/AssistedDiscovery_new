# 🌐 Multi-Airline Format Support

## Overview
Updated AssistedDiscovery to handle different airline XML formats, specifically addressing the **PassengerList vs PaxList** variation found in Iberia vs Lufthansa XML structures.

## Problem Identified

**Different Airlines Use Different Element Names:**
- **Lufthansa/Air France**: `<PaxList><Pax>` format with `<PaxRefID>` references
- **Iberia/British Airways**: `<PassengerList><Passenger>` format with `<ContactInfoRef>` references

## Changes Implemented

### 1. **Enhanced Passenger Combination Detection** (`intelligent_pattern_matcher.py`)

**Before (Limited):**
```python
adults = len(re.findall(r'<PTC>ADT</PTC>', xml_content))
# Only worked with PTC elements
```

**After (Multi-Format):**
```python
# Handle both PTC and other passenger type formats
adults = len(re.findall(r'<PTC>ADT</PTC>', xml_content))

# Fallback: age-based classification from birthdates if no PTC found
if adults + children + infants == 0:
    # Age classification: <2 years = infant, <12 = child, else = adult
```

### 2. **Enhanced Relationship Analysis** (`intelligent_pattern_matcher.py`)

**Before (PaxList only):**
```python
ptc_context_pattern = r'<Pax>.*?<PaxID>([^<]+)</PaxID>.*?<PTC>([^<]+)</PTC>(?:.*?<PaxRefID>([^<]+)</PaxRefID>)?.*?</Pax>'
```

**After (Multi-Format):**
```python
# Handle both Pax and Passenger elements
pax_matches = re.findall(ptc_context_pattern, xml_content, re.DOTALL)
passenger_matches = re.findall(passenger_context_pattern, xml_content, re.DOTALL)

# Also detect ContactInfoRef patterns (Iberia style)
contact_refs = re.findall(r'<ContactInfoRef>([^<]+)</ContactInfoRef>', xml_content)
```

### 3. **Enhanced Pattern Classification** (`airline_pattern_classifier.py`)

**Added Keywords for Multi-Format Recognition:**
```python
'relationship': [
    'contactinforef', 'passengerid', 'passenger.*ref'  # NEW: Iberia-style references
],
'combination': [
    'passengerlist', 'passenger.*list'  # NEW: Iberia-style naming
],
'structural_unique': [
    'iberia.*specific', 'lufthansa.*specific'  # NEW: Airline-specific patterns
]
```

### 4. **Enhanced Pattern Detection** (`identify_pattern_manager.py`)

**Before (PaxList only):**
```python
if "PaxList" not in unknown_source_xml_content:
    st.warning("No PaxList found in XML.")
```

**After (Multi-Format):**
```python
has_passenger_list = any([
    "PaxList" in unknown_source_xml_content,
    "PassengerList" in unknown_source_xml_content,  # NEW: Iberia format
    "paxlist" in unknown_source_xml_content.lower(),
    "passengerlist" in unknown_source_xml_content.lower()
])
```

**Enhanced Pattern Trigger Logic:**
```python
is_passenger_pattern = any([
    "paxlist" in pattern_data["xpath"].lower(),
    "passengerlist" in pattern_data["xpath"].lower(),  # NEW: Iberia format
    "pax" in pattern_data.get("verificationRule", "").lower(),
    "passenger" in pattern_data.get("verificationRule", "").lower()  # NEW
])
```

### 5. **Updated Analysis Prompts**

**Enhanced Prompt (`enhanced_paxlist_pattern_analysis.md`):**
- Added note about handling multiple formats
- Includes PaxRefID **and** ContactInfoRef analysis
- Recognizes element naming as airline fingerprint

**Enhanced Extraction Prompt (`airline_focused_pattern_extraction.md`):**
- Added "Element Naming Variations" as relationship pattern
- Examples include both Lufthansa and Iberia patterns
- Focuses on structural naming differences as airline fingerprints

## Expected Results

### **For Lufthansa XML (PaxList format):**
```
✅ LUFTHANSA_INFANT_ADULT_DEPENDENCY_PATTERN
   - Uses PaxList/Pax structure
   - INF→ADT relationship via PaxRefID
   - Airline Value: 🎯 High (87%)
```

### **For Iberia XML (PassengerList format):**
```
✅ IBERIA_PASSENGER_CONTACT_REFERENCE_PATTERN  
   - Uses PassengerList/Passenger structure
   - ContactInfoRef linking pattern
   - Element naming differentiation
   - Airline Value: 🎯 High (83%)
```

## Airline Format Detection Matrix

| Airline | Format | Passenger List | Passenger Element | Reference Type | ID Attribute |
|---------|--------|----------------|-------------------|----------------|--------------|
| **Lufthansa** | NDC 17.2 | `<PaxList>` | `<Pax>` | `<PaxRefID>` | `<PaxID>` |
| **Iberia** | OVRS 17.2 | `<PassengerList>` | `<Passenger>` | `<ContactInfoRef>` | `PassengerID="..."` |
| **Air France** | NDC 19.1 | `<PaxList>` | `<Pax>` | `<PaxRefID>` | `<PaxID>` |
| **British Airways** | NDC 18.1 | `<PassengerList>` | `<Passenger>` | `<ContactInfoRef>` | `PassengerID="..."` |

## Business Impact

### **Enhanced Airline Identification:**
- **Structural Naming** becomes airline fingerprint
- **Reference Patterns** differentiate carrier implementations  
- **Format Variations** help identify airline even without explicit codes

### **Improved Pattern Quality:**
- System recognizes **PassengerList** as high-value airline pattern
- **ContactInfoRef** patterns get proper airline classification scores
- **Element naming variations** contribute to airline fingerprinting

### **Better Coverage:**
- Supports major airline NDC implementations
- Handles both IATA NDC and airline-specific OVRS formats
- Future-proof for other airline format variations

## Testing Scenarios

### **Test Case 1: Lufthansa (PaxList format)**
```xml
<PaxList>
  <Pax>
    <PaxID>PAX3</PaxID>
    <PTC>INF</PTC>
    <PaxRefID>PAX2</PaxRefID>
  </Pax>
</PaxList>
```
**Expected:** Detects INF→ADT relationship, PaxList naming pattern

### **Test Case 2: Iberia (PassengerList format)**  
```xml
<PassengerList>
  <Passenger PassengerID="PAX1">
    <PTC>ADT</PTC>
    <ContactInfoRef>CI1PAX1</ContactInfoRef>
  </Passenger>
</PassengerList>
```
**Expected:** Detects ContactInfoRef pattern, PassengerList naming pattern

## Future Enhancements

1. **Additional Format Support**: American Airlines, Delta variations
2. **Smart Format Detection**: Auto-detect airline from element naming
3. **Format-Specific Validation**: Different rules per airline format
4. **Pattern Migration**: Convert between airline formats

---

**Result:** Your AssistedDiscovery system now handles **multiple airline XML formats** and uses format variations as additional airline fingerprinting signals, making identification more robust across different carrier implementations.