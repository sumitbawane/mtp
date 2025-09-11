"""
Information Minimality Testing Framework
Tests information sufficiency by removing sentences and checking solvability
"""

import re
import itertools
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scenario_core import Transfer, Agent, Scenario
from constraint_system import ConstraintSystemBuilder, UniquenessVerifier


@dataclass
class SentenceInfo:
    """Information about a sentence in the problem"""
    sentence_id: str
    content: str
    information_type: str  # 'initial_state', 'transfer', 'constraint', 'question'
    agents_mentioned: Set[str]
    objects_mentioned: Set[str]
    quantities_mentioned: List[int]
    is_essential: bool = False


@dataclass
class MinimalityResult:
    """Result of minimality testing"""
    is_minimal: bool
    redundant_sentences: List[str]
    essential_sentences: List[str]
    information_sufficiency_score: float
    suggested_removals: List[str]
    suggested_additions: List[str]
    detailed_analysis: Dict[str, Any]


class MinimalityTester:
    """Tests information minimality and sufficiency in AWP problems"""
    
    def __init__(self):
        self.constraint_builder = ConstraintSystemBuilder()
        self.uniqueness_verifier = UniquenessVerifier()
        
        # Patterns for identifying information types
        self.info_patterns = {
            'initial_state': [
                r'initially,?\s+(\w+)\s+has?\s+(\d+)\s+(\w+)s?',
                r'(\w+)\s+starts?\s+with\s+(\d+)\s+(\w+)s?',
                r'at\s+first,?\s+(\w+)\s+has?\s+(\d+)\s+(\w+)s?'
            ],
            'transfer': [
                r'(\w+)\s+(?:gives?|transfers?|sends?)\s+(\d+)\s+(\w+)s?\s+to\s+(\w+)',
                r'(\w+)\s+receives?\s+(\d+)\s+(\w+)s?\s+from\s+(\w+)'
            ],
            'constraint': [
                r'at\s+the\s+end,?\s+(\w+)\s+has?\s+(\d+)\s+(\w+)s?',
                r'finally,?\s+(\w+)\s+has?\s+(\d+)\s+(\w+)s?',
                r'(\w+)\s+ends?\s+(?:up\s+)?with\s+(\d+)\s+(\w+)s?'
            ],
            'question': [
                r'how\s+many\s+(\w+)s?\s+does\s+(\w+)\s+have',
                r'what\s+is\s+the\s+(?:total|sum|number)',
                r'how\s+much\s+(?:did|was)\s+transferred'
            ]
        }
    
    def test_minimality(self, question_text: str, scenario: Scenario,
                       masked_info: Dict[str, Any] = None) -> MinimalityResult:
        """
        Test information minimality of a question
        
        Args:
            question_text: Complete question text
            scenario: AWP scenario for constraint building
            masked_info: Information about masking applied
            
        Returns:
            MinimalityResult with detailed analysis
        """
        
        # Parse sentences and extract information
        sentences = self._parse_sentences(question_text)
        sentence_info = self._analyze_sentences(sentences)
        
        # Test baseline solvability
        baseline_solvable = self._test_solvability(question_text, scenario, masked_info)
        
        if not baseline_solvable:
            return MinimalityResult(
                is_minimal=False,
                redundant_sentences=[],
                essential_sentences=[],
                information_sufficiency_score=0.0,
                suggested_removals=[],
                suggested_additions=["Problem is not solvable - add more constraints"],
                detailed_analysis={'error': 'Baseline problem is not solvable'}
            )
        
        # Test sentence removal
        redundant_sentences = self._find_redundant_sentences(sentences, scenario, masked_info)
        essential_sentences = self._find_essential_sentences(sentences, scenario, masked_info)
        
        # Calculate information sufficiency
        sufficiency_score = self._calculate_sufficiency_score(sentence_info, redundant_sentences)
        
        # Generate suggestions
        removal_suggestions = self._suggest_removals(redundant_sentences, sentence_info)
        addition_suggestions = self._suggest_additions(sentence_info, scenario)
        
        # Detailed analysis
        detailed_analysis = self._create_detailed_analysis(
            sentence_info, redundant_sentences, essential_sentences, sufficiency_score
        )
        
        is_minimal = len(redundant_sentences) == 0
        
        return MinimalityResult(
            is_minimal=is_minimal,
            redundant_sentences=redundant_sentences,
            essential_sentences=essential_sentences,
            information_sufficiency_score=sufficiency_score,
            suggested_removals=removal_suggestions,
            suggested_additions=addition_suggestions,
            detailed_analysis=detailed_analysis
        )
    
    def _parse_sentences(self, text: str) -> List[str]:
        """Parse text into individual sentences"""
        # Split by periods, exclamation marks, question marks
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Filter very short fragments
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _analyze_sentences(self, sentences: List[str]) -> List[SentenceInfo]:
        """Analyze each sentence for information content"""
        sentence_info = []
        
        for i, sentence in enumerate(sentences):
            # Classify information type
            info_type = self._classify_sentence_type(sentence)
            
            # Extract mentioned entities
            agents = self._extract_agents(sentence)
            objects = self._extract_objects(sentence)  
            quantities = self._extract_quantities(sentence)
            
            info = SentenceInfo(
                sentence_id=f"sent_{i}",
                content=sentence,
                information_type=info_type,
                agents_mentioned=agents,
                objects_mentioned=objects,
                quantities_mentioned=quantities
            )
            
            sentence_info.append(info)
        
        return sentence_info
    
    def _classify_sentence_type(self, sentence: str) -> str:
        """Classify the type of information in a sentence"""
        sentence_lower = sentence.lower()
        
        # Check each pattern type
        for info_type, patterns in self.info_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    return info_type
        
        return 'other'
    
    def _extract_agents(self, sentence: str) -> Set[str]:
        """Extract agent names from sentence"""
        # Simple approach - look for capitalized words (agent names)
        agents = set()
        words = sentence.split()
        
        for word in words:
            # Remove punctuation and check if capitalized
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 1:
                # Check if it looks like a name (not at start of sentence)
                if word != words[0] or sentence.startswith(clean_word):
                    agents.add(clean_word)
        
        return agents
    
    def _extract_objects(self, sentence: str) -> Set[str]:
        """Extract object type names from sentence"""
        # Look for common object words after numbers
        pattern = r'\d+\s+(\w+)s?'
        matches = re.findall(pattern, sentence.lower())
        
        objects = set()
        for match in matches:
            # Filter out common words that aren't objects
            if match not in ['time', 'times', 'way', 'ways', 'thing', 'things']:
                objects.add(match)
        
        return objects
    
    def _extract_quantities(self, sentence: str) -> List[int]:
        """Extract numerical quantities from sentence"""
        numbers = re.findall(r'\b\d+\b', sentence)
        return [int(num) for num in numbers]
    
    def _find_redundant_sentences(self, sentences: List[str], scenario: Scenario,
                                masked_info: Dict[str, Any] = None) -> List[str]:
        """Find sentences that can be removed without affecting solvability"""
        redundant = []
        
        # Test removing each sentence individually
        for i, sentence in enumerate(sentences):
            # Create text without this sentence
            remaining_sentences = sentences[:i] + sentences[i+1:]
            test_text = '. '.join(remaining_sentences) + '.'
            
            # Test if still solvable
            if self._test_solvability(test_text, scenario, masked_info):
                redundant.append(sentence)
        
        # Test combinations of removals to find maximal redundant set
        if len(redundant) > 1:
            # Try removing combinations of redundant sentences
            for r in range(2, min(len(redundant) + 1, 4)):  # Limit combinations to avoid exponential explosion
                for combo in itertools.combinations(redundant, r):
                    # Remove this combination
                    remaining = [s for s in sentences if s not in combo]
                    test_text = '. '.join(remaining) + '.'
                    
                    if self._test_solvability(test_text, scenario, masked_info):
                        # All of these can be removed together
                        return list(combo)
        
        return redundant
    
    def _find_essential_sentences(self, sentences: List[str], scenario: Scenario,
                                masked_info: Dict[str, Any] = None) -> List[str]:
        """Find sentences that are essential for solvability"""
        essential = []
        
        for i, sentence in enumerate(sentences):
            # Create text without this sentence
            remaining_sentences = sentences[:i] + sentences[i+1:]
            test_text = '. '.join(remaining_sentences) + '.'
            
            # Test if still solvable
            if not self._test_solvability(test_text, scenario, masked_info):
                essential.append(sentence)
        
        return essential
    
    def _test_solvability(self, question_text: str, scenario: Scenario,
                        masked_info: Dict[str, Any] = None) -> bool:
        """Test if a question text provides sufficient information for solvability"""
        
        try:
            # Build constraint system from scenario and masking info
            constraint_system = self.constraint_builder.build_from_scenario(scenario, masked_info)
            
            # Verify uniqueness
            verification_result = self.uniqueness_verifier.verify_uniqueness(constraint_system)
            
            return verification_result.is_unique and verification_result.solvable
            
        except Exception:
            return False
    
    def _calculate_sufficiency_score(self, sentence_info: List[SentenceInfo],
                                   redundant_sentences: List[str]) -> float:
        """Calculate information sufficiency score (0-1)"""
        
        if not sentence_info:
            return 0.0
        
        total_sentences = len(sentence_info)
        redundant_count = len(redundant_sentences)
        essential_count = total_sentences - redundant_count
        
        # Score based on ratio of essential to total information
        base_score = essential_count / total_sentences if total_sentences > 0 else 0
        
        # Adjust based on information types present
        info_types = set(info.information_type for info in sentence_info)
        required_types = {'initial_state', 'transfer', 'constraint'}
        
        type_coverage = len(info_types.intersection(required_types)) / len(required_types)
        
        # Combined score
        sufficiency_score = (base_score * 0.7) + (type_coverage * 0.3)
        
        return min(1.0, sufficiency_score)
    
    def _suggest_removals(self, redundant_sentences: List[str],
                        sentence_info: List[SentenceInfo]) -> List[str]:
        """Suggest specific sentence removals"""
        suggestions = []
        
        for sentence in redundant_sentences:
            # Find the sentence info
            info = next((si for si in sentence_info if si.content == sentence), None)
            if info:
                reason = f"Remove: '{sentence[:50]}...' - {info.information_type} information is redundant"
                suggestions.append(reason)
        
        return suggestions
    
    def _suggest_additions(self, sentence_info: List[SentenceInfo],
                         scenario: Scenario) -> List[str]:
        """Suggest information that might need to be added"""
        suggestions = []
        
        # Check for missing information types
        present_types = set(info.information_type for info in sentence_info)
        
        if 'constraint' not in present_types:
            suggestions.append("Consider adding a final state constraint for better solvability")
        
        if 'initial_state' not in present_types:
            suggestions.append("Consider adding initial inventory information")
        
        # Check for agent coverage
        mentioned_agents = set()
        for info in sentence_info:
            mentioned_agents.update(info.agents_mentioned)
        
        scenario_agents = set(agent.name for agent in scenario.agents)
        missing_agents = scenario_agents - mentioned_agents
        
        if missing_agents:
            suggestions.append(f"Agents {missing_agents} are not mentioned in the problem text")
        
        return suggestions
    
    def _create_detailed_analysis(self, sentence_info: List[SentenceInfo],
                                redundant_sentences: List[str],
                                essential_sentences: List[str],
                                sufficiency_score: float) -> Dict[str, Any]:
        """Create detailed analysis breakdown"""
        
        return {
            'total_sentences': len(sentence_info),
            'essential_count': len(essential_sentences),
            'redundant_count': len(redundant_sentences),
            'sufficiency_score': sufficiency_score,
            'information_types': {
                info_type: len([si for si in sentence_info if si.information_type == info_type])
                for info_type in set(si.information_type for si in sentence_info)
            },
            'sentence_breakdown': [
                {
                    'content': info.content,
                    'type': info.information_type,
                    'agents': list(info.agents_mentioned),
                    'objects': list(info.objects_mentioned),
                    'quantities': info.quantities_mentioned,
                    'status': 'essential' if info.content in essential_sentences
                             else 'redundant' if info.content in redundant_sentences
                             else 'unclear'
                }
                for info in sentence_info
            ]
        }
    
    def optimize_information_content(self, question_text: str, scenario: Scenario,
                                   masked_info: Dict[str, Any] = None) -> Tuple[str, MinimalityResult]:
        """Optimize question by removing redundant information"""
        
        result = self.test_minimality(question_text, scenario, masked_info)
        
        if result.is_minimal:
            return question_text, result
        
        # Remove redundant sentences
        sentences = self._parse_sentences(question_text)
        optimized_sentences = [s for s in sentences if s not in result.redundant_sentences]
        
        optimized_text = '. '.join(optimized_sentences) + '.'
        
        return optimized_text, result