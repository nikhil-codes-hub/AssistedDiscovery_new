"""
Airline Pattern Classifier - Determines which patterns are valuable for airline identification
"""
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class PatternValueType(Enum):
    """Types of pattern values for airline identification"""
    HIGH_VALUE = "high"           # Critical for airline identification
    MODERATE_VALUE = "moderate"   # Somewhat useful for airline identification
    LOW_VALUE = "low"            # Not useful for airline identification
    NOISE = "noise"              # Actually harmful/confusing for airline identification

@dataclass
class PatternClassification:
    """Classification result for a pattern"""
    value_type: PatternValueType
    score: float  # 0-100
    reasons: List[str]
    category: str  # "relationship", "combination", "structural", "generic"

class AirlinePatternClassifier:
    """
    Classifies extracted patterns based on their value for airline identification.
    Filters out generic patterns and promotes airline-specific fingerprints.
    """
    
    def __init__(self):
        # Keywords that indicate high-value airline-differentiating patterns
        self.high_value_keywords = {
            'relationship': [
                'paxrefid', 'reference', 'parent-child', 'relationship', 'linking',
                'infant.*adult', 'adult.*infant', 'dependency', 'association',
                'contactinforef', 'passengerid', 'passenger.*ref'
            ],
            'combination': [
                'combination', 'mix', 'multiple.*pax', 'passenger.*types', 
                'adt.*chd.*inf', 'adult.*child.*infant', 'composition',
                'passengerlist', 'passenger.*list'
            ],
            'structural_unique': [
                'airline.*specific', 'unique.*structure', 'distinguishing',
                'api.*version', 'carrier.*specific', 'ndc.*pattern',
                'iberia.*specific', 'lufthansa.*specific', 'airfrance.*specific'
            ]
        }
        
        # Keywords that indicate low-value generic patterns
        self.low_value_keywords = [
            'individual.*details', 'personal.*information', 'basic.*structure',
            'name.*field', 'birthdate', 'gender', 'title', 'surname', 'givenname',
            'individual.*node', 'passenger.*details', 'contact.*info',
            'standard.*field', 'common.*element', 'generic.*pattern'
        ]
        
        # Keywords that indicate noise patterns
        self.noise_keywords = [
            'validation.*only', 'format.*check', 'field.*presence',
            'element.*exists', 'required.*field', 'data.*type'
        ]
    
    def classify_pattern(self, pattern: Dict[str, Any]) -> PatternClassification:
        """
        Classify a single pattern based on its airline identification value
        
        Args:
            pattern: Dictionary containing pattern info (name, description, path, prompt)
            
        Returns:
            PatternClassification with value type, score, and reasons
        """
        name = pattern.get('name', '').lower()
        description = pattern.get('description', '').lower()
        path = pattern.get('path', '').lower()
        prompt = pattern.get('prompt', '').lower()
        
        # Combine all text for analysis
        full_text = f"{name} {description} {path} {prompt}"
        
        # Start with base score
        score = 50.0
        reasons = []
        category = "generic"
        
        # Check for high-value patterns
        relationship_score = self._check_relationship_patterns(full_text)
        combination_score = self._check_combination_patterns(full_text)
        structural_score = self._check_structural_uniqueness(full_text)
        
        # Check for low-value/noise patterns
        generic_penalty = self._check_generic_patterns(full_text)
        noise_penalty = self._check_noise_patterns(full_text)
        
        # Calculate final score
        max_high_value = max(relationship_score, combination_score, structural_score)
        score += max_high_value - generic_penalty - noise_penalty
        
        # Determine category and reasons
        if relationship_score > 30:
            category = "relationship"
            reasons.append(f"Contains relationship patterns (score: {relationship_score})")
        elif combination_score > 30:
            category = "combination"
            reasons.append(f"Contains combination patterns (score: {combination_score})")
        elif structural_score > 30:
            category = "structural"
            reasons.append(f"Contains structural uniqueness (score: {structural_score})")
        
        if generic_penalty > 20:
            reasons.append(f"Generic pattern penalty applied (-{generic_penalty})")
        if noise_penalty > 20:
            reasons.append(f"Noise pattern penalty applied (-{noise_penalty})")
        
        # Determine value type based on final score
        if score >= 80:
            value_type = PatternValueType.HIGH_VALUE
        elif score >= 60:
            value_type = PatternValueType.MODERATE_VALUE
        elif score >= 30:
            value_type = PatternValueType.LOW_VALUE
        else:
            value_type = PatternValueType.NOISE
            
        return PatternClassification(
            value_type=value_type,
            score=min(100, max(0, score)),
            reasons=reasons,
            category=category
        )
    
    def _check_relationship_patterns(self, text: str) -> float:
        """Check for passenger relationship patterns"""
        score = 0.0
        
        for keyword in self.high_value_keywords['relationship']:
            if re.search(keyword, text, re.IGNORECASE):
                score += 15.0
        
        # Specific high-value relationship indicators
        if 'paxrefid' in text and ('infant' in text or 'adult' in text):
            score += 25.0  # INF-ADT relationships are gold for airline ID
        
        if 'reference' in text and 'pax' in text:
            score += 20.0
            
        if re.search(r'parent.*child|child.*parent', text, re.IGNORECASE):
            score += 20.0
            
        return min(50.0, score)
    
    def _check_combination_patterns(self, text: str) -> float:
        """Check for passenger combination patterns"""
        score = 0.0
        
        for keyword in self.high_value_keywords['combination']:
            if re.search(keyword, text, re.IGNORECASE):
                score += 15.0
        
        # Look for passenger type combinations
        passenger_types = ['adt', 'chd', 'inf', 'adult', 'child', 'infant']
        type_count = sum(1 for ptype in passenger_types if ptype in text)
        
        if type_count >= 2:
            score += 20.0  # Multiple passenger types = combination pattern
            
        if 'mix' in text or 'combination' in text:
            score += 15.0
            
        return min(50.0, score)
    
    def _check_structural_uniqueness(self, text: str) -> float:
        """Check for airline-specific structural patterns"""
        score = 0.0
        
        for keyword in self.high_value_keywords['structural_unique']:
            if re.search(keyword, text, re.IGNORECASE):
                score += 15.0
        
        # API-specific indicators
        if re.search(r'api.*version|version.*\d+\.\d+', text, re.IGNORECASE):
            score += 20.0
            
        # Airline-specific structure indicators
        if 'unique' in text and ('structure' in text or 'pattern' in text):
            score += 20.0
            
        return min(50.0, score)
    
    def _check_generic_patterns(self, text: str) -> float:
        """Check for generic, non-differentiating patterns"""
        penalty = 0.0
        
        for keyword in self.low_value_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                penalty += 10.0
        
        # Heavy penalty for basic field patterns
        basic_fields = ['name', 'birthdate', 'gender', 'title', 'surname', 'givenname']
        field_count = sum(1 for field in basic_fields if field in text)
        
        if field_count >= 3:
            penalty += 30.0  # This is just basic passenger info, not airline-specific
            
        return min(50.0, penalty)
    
    def _check_noise_patterns(self, text: str) -> float:
        """Check for noise patterns that don't help airline identification"""
        penalty = 0.0
        
        for keyword in self.noise_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                penalty += 15.0
        
        # Patterns focused only on validation without business logic
        if 'validation' in text and not any(x in text for x in ['relationship', 'combination', 'unique']):
            penalty += 20.0
            
        return min(50.0, penalty)
    
    def filter_patterns(self, patterns: List[Dict[str, Any]], 
                       min_score: float = 60.0) -> Tuple[List[Dict[str, Any]], List[PatternClassification]]:
        """
        Filter patterns to keep only airline-differentiating ones
        
        Args:
            patterns: List of extracted patterns
            min_score: Minimum score to keep a pattern (0-100)
            
        Returns:
            Tuple of (filtered_patterns, classifications)
        """
        filtered_patterns = []
        classifications = []
        
        for pattern in patterns:
            classification = self.classify_pattern(pattern)
            classifications.append(classification)
            
            if classification.score >= min_score:
                # Add classification info to pattern
                pattern_with_score = pattern.copy()
                pattern_with_score['airline_value_score'] = classification.score
                pattern_with_score['airline_value_type'] = classification.value_type.value
                pattern_with_score['airline_category'] = classification.category
                pattern_with_score['classification_reasons'] = classification.reasons
                
                filtered_patterns.append(pattern_with_score)
        
        return filtered_patterns, classifications
    
    def get_pattern_recommendations(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide recommendations for improving pattern extraction
        
        Args:
            patterns: List of extracted patterns
            
        Returns:
            Dictionary with recommendations and statistics
        """
        classifications = [self.classify_pattern(p) for p in patterns]
        
        # Statistics
        total_patterns = len(patterns)
        high_value = len([c for c in classifications if c.value_type == PatternValueType.HIGH_VALUE])
        moderate_value = len([c for c in classifications if c.value_type == PatternValueType.MODERATE_VALUE])
        low_value = len([c for c in classifications if c.value_type == PatternValueType.LOW_VALUE])
        noise = len([c for c in classifications if c.value_type == PatternValueType.NOISE])
        
        # Category analysis
        categories = {}
        for c in classifications:
            categories[c.category] = categories.get(c.category, 0) + 1
        
        # Recommendations
        recommendations = []
        
        if noise > total_patterns * 0.3:
            recommendations.append("⚠️ High noise ratio - consider refining extraction to focus on airline-specific patterns")
        
        if high_value == 0:
            recommendations.append("🎯 No high-value patterns found - focus on relationship and combination patterns")
        
        if categories.get('relationship', 0) == 0:
            recommendations.append("🔗 Missing relationship patterns - look for PaxRefID and passenger dependencies")
            
        if categories.get('combination', 0) == 0:
            recommendations.append("👥 Missing combination patterns - analyze passenger type mixes (ADT+CHD+INF)")
        
        return {
            'statistics': {
                'total_patterns': total_patterns,
                'high_value': high_value,
                'moderate_value': moderate_value, 
                'low_value': low_value,
                'noise': noise,
                'categories': categories
            },
            'recommendations': recommendations,
            'efficiency_score': ((high_value + moderate_value) / max(total_patterns, 1)) * 100
        }