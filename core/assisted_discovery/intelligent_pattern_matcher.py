import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from core.common.logging_manager import get_logger

@dataclass
class PassengerCombination:
    """Represents a passenger type combination pattern"""
    adults: int
    children: int  
    infants: int
    pattern_signature: str
    
    def __post_init__(self):
        if not self.pattern_signature:
            parts = []
            if self.adults > 0: parts.append(f"{self.adults}ADT")
            if self.children > 0: parts.append(f"{self.children}CHD") 
            if self.infants > 0: parts.append(f"{self.infants}INF")
            self.pattern_signature = "+".join(parts) if parts else "EMPTY"

@dataclass 
class RelationshipPattern:
    """Represents airline-specific relationship patterns"""
    direction: str  # "INF→ADT", "ADT→INF", "BIDIRECTIONAL", "NONE"
    reference_structure: str
    linking_rules: str
    confidence: float

@dataclass
class AirlineFingerprint:
    """Complete airline pattern fingerprint"""
    airline_code: str
    api_version: str
    passenger_combination: PassengerCombination
    relationship_pattern: RelationshipPattern
    structural_signature: str
    distinguishing_features: List[str]
    confidence_score: float

class IntelligentPatternMatcher:
    """
    Enhanced pattern matcher that can intelligently match passenger combinations
    and airline-specific relationship patterns.
    """
    
    def __init__(self):
        self.logger = get_logger("intelligent_pattern_matcher")
        self.known_patterns: Dict[str, List[AirlineFingerprint]] = {}
        self.combination_patterns: Dict[str, List[PassengerCombination]] = {}
        
    def learn_pattern(self, airline_fingerprint: AirlineFingerprint):
        """Learn a new airline pattern"""
        airline_key = f"{airline_fingerprint.airline_code}_{airline_fingerprint.api_version}"
        
        if airline_key not in self.known_patterns:
            self.known_patterns[airline_key] = []
        
        self.known_patterns[airline_key].append(airline_fingerprint)
        
        # Also store by combination pattern for intelligent matching
        combo_key = airline_fingerprint.passenger_combination.pattern_signature
        if combo_key not in self.combination_patterns:
            self.combination_patterns[combo_key] = []
        
        self.combination_patterns[combo_key].append(airline_fingerprint.passenger_combination)
        self.logger.info(f"Learned new pattern for {airline_key}: {combo_key}")
    
    def extract_passenger_combination(self, xml_content: str) -> PassengerCombination:
        """Extract passenger combination from XML content - handles multiple airline formats"""
        # Handle both PTC and other passenger type formats
        adults = len(re.findall(r'<PTC>ADT</PTC>', xml_content))
        children = len(re.findall(r'<PTC>CHD</PTC>', xml_content))
        infants = len(re.findall(r'<PTC>INF</PTC>', xml_content))
        
        # Handle alternative formats (e.g., some airlines use different elements)
        # Also check for passenger elements without PTC but with age-based classification
        if adults + children + infants == 0:
            # Try alternative passenger detection methods
            passenger_elements = re.findall(r'<Passenger[^>]*>', xml_content)
            birthdate_pattern = r'<Birthdate>(\d{4}-\d{2}-\d{2})</Birthdate>'
            birthdates = re.findall(birthdate_pattern, xml_content)
            
            # Basic age classification if we have birthdates
            if birthdates:
                from datetime import datetime
                current_year = datetime.now().year
                for birthdate in birthdates:
                    birth_year = int(birthdate.split('-')[0])
                    age = current_year - birth_year
                    
                    if age < 2:
                        infants += 1
                    elif age < 12:
                        children += 1
                    else:
                        adults += 1
        
        return PassengerCombination(adults, children, infants, "")
    
    def analyze_relationships(self, xml_content: str) -> RelationshipPattern:
        """Analyze passenger relationship patterns in XML - handles multiple airline formats"""
        # Find all reference patterns (both PaxRefID and other reference types)
        pax_ref_pattern = r'<PaxRefID>([^<]+)</PaxRefID>'
        pax_refs = re.findall(pax_ref_pattern, xml_content)
        
        # Also look for other reference patterns
        contact_ref_pattern = r'<ContactInfoRef>([^<]+)</ContactInfoRef>'
        contact_refs = re.findall(contact_ref_pattern, xml_content)
        
        # Find PTC patterns with context (handle both Pax and Passenger elements)
        ptc_context_pattern = r'<Pax>.*?<PaxID>([^<]+)</PaxID>.*?<PTC>([^<]+)</PTC>(?:.*?<PaxRefID>([^<]+)</PaxRefID>)?.*?</Pax>'
        pax_matches = re.findall(ptc_context_pattern, xml_content, re.DOTALL)
        
        # Handle PassengerList format (Iberia style)
        passenger_context_pattern = r'<Passenger[^>]*PassengerID="([^"]+)"[^>]*>.*?<PTC>([^<]+)</PTC>(?:.*?<PaxRefID>([^<]+)</PaxRefID>)?.*?</Passenger>'
        passenger_matches = re.findall(passenger_context_pattern, xml_content, re.DOTALL)
        
        # Combine matches from both formats
        matches = pax_matches + passenger_matches
        
        # Analyze relationship direction
        infant_to_adult_refs = []
        adult_to_infant_refs = []
        
        pax_info = {}  # pax_id -> (ptc, ref_id)
        for match in matches:
            pax_id, ptc, ref_id = match
            pax_info[pax_id] = (ptc, ref_id if ref_id else None)
        
        # Determine relationship direction
        for pax_id, (ptc, ref_id) in pax_info.items():
            if ptc == "INF" and ref_id:
                ref_ptc = pax_info.get(ref_id, (None, None))[0]
                if ref_ptc == "ADT":
                    infant_to_adult_refs.append((pax_id, ref_id))
            elif ptc == "ADT" and ref_id:
                ref_ptc = pax_info.get(ref_id, (None, None))[0]
                if ref_ptc == "INF":
                    adult_to_infant_refs.append((pax_id, ref_id))
        
        # Determine direction
        direction = "NONE"
        if infant_to_adult_refs and not adult_to_infant_refs:
            direction = "INF→ADT"
        elif adult_to_infant_refs and not infant_to_adult_refs:
            direction = "ADT→INF" 
        elif infant_to_adult_refs and adult_to_infant_refs:
            direction = "BIDIRECTIONAL"
        
        # Generate reference structure description
        total_refs = len(pax_refs) + len(contact_refs)
        ref_structure = f"Found {len(pax_refs)} PaxRefID elements, {len(contact_refs)} ContactInfoRef elements"
        if infant_to_adult_refs:
            ref_structure += f", {len(infant_to_adult_refs)} INF→ADT links"
        if adult_to_infant_refs:
            ref_structure += f", {len(adult_to_infant_refs)} ADT→INF links"
            
        # Generate linking rules
        linking_rules = []
        if direction == "INF→ADT":
            linking_rules.append("Each infant references exactly one adult")
        elif direction == "ADT→INF":
            linking_rules.append("Each adult references associated infant")
            
        return RelationshipPattern(
            direction=direction,
            reference_structure=ref_structure, 
            linking_rules="; ".join(linking_rules),
            confidence=0.9 if direction != "NONE" else 0.1
        )
    
    def intelligent_match(self, unknown_combination: PassengerCombination, 
                         unknown_relationship: RelationshipPattern,
                         similarity_threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Intelligently match unknown patterns against known airline patterns.
        Returns list of (airline_key, confidence_score) tuples.
        """
        matches = []
        
        for airline_key, fingerprints in self.known_patterns.items():
            for fingerprint in fingerprints:
                confidence = self._calculate_pattern_similarity(
                    unknown_combination, unknown_relationship,
                    fingerprint.passenger_combination, fingerprint.relationship_pattern
                )
                
                if confidence >= similarity_threshold:
                    matches.append((airline_key, confidence))
        
        # Sort by confidence score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _calculate_pattern_similarity(self, 
                                    unknown_combo: PassengerCombination,
                                    unknown_rel: RelationshipPattern,
                                    known_combo: PassengerCombination, 
                                    known_rel: RelationshipPattern) -> float:
        """Calculate similarity between two patterns"""
        
        # Combination similarity (40% weight)
        combo_score = self._combination_similarity(unknown_combo, known_combo)
        
        # Relationship similarity (60% weight) - more important for airline identification
        rel_score = self._relationship_similarity(unknown_rel, known_rel)
        
        return (combo_score * 0.4) + (rel_score * 0.6)
    
    def _combination_similarity(self, combo1: PassengerCombination, 
                              combo2: PassengerCombination) -> float:
        """Calculate passenger combination similarity"""
        # Exact match gets 1.0
        if (combo1.adults == combo2.adults and 
            combo1.children == combo2.children and 
            combo1.infants == combo2.infants):
            return 1.0
        
        # Partial matches with decreasing scores
        total1 = combo1.adults + combo1.children + combo1.infants
        total2 = combo2.adults + combo2.children + combo2.infants
        
        if total1 == 0 or total2 == 0:
            return 0.0
        
        # Calculate individual type similarities
        adult_sim = 1.0 - abs(combo1.adults - combo2.adults) / max(combo1.adults, combo2.adults, 1)
        child_sim = 1.0 - abs(combo1.children - combo2.children) / max(combo1.children, combo2.children, 1)  
        infant_sim = 1.0 - abs(combo1.infants - combo2.infants) / max(combo1.infants, combo2.infants, 1)
        
        # Weighted average (infants are most important for airline identification)
        return (adult_sim * 0.3) + (child_sim * 0.2) + (infant_sim * 0.5)
    
    def _relationship_similarity(self, rel1: RelationshipPattern, 
                               rel2: RelationshipPattern) -> float:
        """Calculate relationship pattern similarity"""
        
        # Direction match is most important
        direction_score = 1.0 if rel1.direction == rel2.direction else 0.3
        
        # Reference structure similarity (simple string matching for now)
        ref_score = 0.5 if rel1.reference_structure in rel2.reference_structure or \
                           rel2.reference_structure in rel1.reference_structure else 0.1
                           
        # Linking rules similarity
        rules_score = 0.5 if rel1.linking_rules == rel2.linking_rules else 0.2
        
        return (direction_score * 0.6) + (ref_score * 0.2) + (rules_score * 0.2)
    
    def suggest_new_combinations(self, base_combination: PassengerCombination) -> List[PassengerCombination]:
        """
        Suggest possible new combinations based on known patterns.
        This handles the "intelligent inference" for unseen combinations.
        """
        suggestions = []
        
        # Generate logical variations
        # Add one more of each type
        if base_combination.adults > 0:
            suggestions.append(PassengerCombination(
                base_combination.adults + 1, base_combination.children, base_combination.infants, ""
            ))
        
        if base_combination.children > 0:
            suggestions.append(PassengerCombination(
                base_combination.adults, base_combination.children + 1, base_combination.infants, ""
            ))
            
        if base_combination.infants > 0:
            suggestions.append(PassengerCombination(
                base_combination.adults, base_combination.children, base_combination.infants + 1, ""
            ))
        
        # Common travel combinations
        common_patterns = [
            PassengerCombination(2, 0, 0, ""),  # 2 adults
            PassengerCombination(2, 1, 0, ""),  # Family with 1 child
            PassengerCombination(2, 2, 0, ""),  # Family with 2 children
            PassengerCombination(2, 0, 1, ""),  # Couple with infant
            PassengerCombination(2, 1, 1, ""),  # Family with child and infant
            PassengerCombination(1, 0, 1, ""),  # Single parent with infant
        ]
        
        suggestions.extend(common_patterns)
        
        # Remove duplicates and base combination
        unique_suggestions = []
        seen_signatures = {base_combination.pattern_signature}
        
        for suggestion in suggestions:
            if suggestion.pattern_signature not in seen_signatures:
                unique_suggestions.append(suggestion)
                seen_signatures.add(suggestion.pattern_signature)
        
        return unique_suggestions[:10]  # Return top 10 suggestions