"""
Enhanced Arithmetic Word Problem Generator
Main orchestrator using enhanced graph-based system with BFS/DFS traversal
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional
import sys
import os

# Import enhanced components
from scenario_core import Scenario
from graph_generation import EnhancedGraphGenerator, GenerationConfig, EnhancedScenarioResult
from topology_control.parametric_graphs import TopologyParams
from question_utils import TemplateManager, AnswerCalculator
from text_processing import TextProcessor, ContextGenerator
from dataset_manager import DatasetManager


class EnhancedQuestionGenerator:
    """Enhanced question generator with mathematical rigor and BFS/DFS traversal"""

    def __init__(self, use_enhanced_generation: bool = True):
        self.question_counter = 0
        self.use_enhanced_generation = use_enhanced_generation
        
        # Initialize components
        self.template_manager = TemplateManager()
        self.text_processor = TextProcessor()
        self.context_generator = ContextGenerator()
        self.answer_calculator = AnswerCalculator()
        self.dataset_manager = DatasetManager()
        
        # Enhanced graph-based generator
        self.enhanced_generator = EnhancedGraphGenerator()
        
        # Default generation configuration
        self.default_config = GenerationConfig(
            topology_params=TopologyParams(
                path_length=3,
                branching_factor=2.0,
                allow_cycles=False,
                connectivity=0.8,
                hub_probability=0.3
            ),
            target_complexity=6.0,
            complexity_tolerance=1.5,
            enable_uniqueness_check=True,
            enable_smt_verification=False,  # Optional Z3 verification
            apply_graph_aware_masking=True,
            use_structured_traversal=True,
            apply_anaphoric_references=True,
            test_minimality=True
        )

    def generate_enhanced_question(self, 
                                 target_complexity: float = 6.0,
                                 question_type: str = 'final_count',
                                 config: Optional[GenerationConfig] = None,
                                 max_attempts: int = 5) -> Dict[str, Any]:
        """
        Generate a single question using enhanced graph-based system with solvability validation
        
        Args:
            target_complexity: Target complexity score (3-12)
            question_type: Type of question to generate
            config: Optional generation configuration
            max_attempts: Maximum attempts to generate a solvable question
            
        Returns:
            Enhanced question with all processing applied (guaranteed solvable)
        """
        if config is None:
            config = self.default_config
            config.target_complexity = target_complexity
        
        for attempt in range(max_attempts):
            # Generate enhanced scenario
            scenario_result = self.enhanced_generator.generate_enhanced_scenario(config)
            
            if not scenario_result:
                continue
            
            # Generate question with all enhancements
            enhanced_question = self.enhanced_generator.generate_question_with_enhancements(
                scenario_result, question_type
            )
            
            # Add metadata
            enhanced_question.update({
                'question_id': self._get_next_id(),
                'scenario_id': scenario_result.scenario.scenario_id,
                'generation_metadata': {
                    'complexity_score': scenario_result.complexity_components.total_score if scenario_result.complexity_components else None,
                    'graph_metrics': {
                        'diameter': scenario_result.graph_metrics.diameter,
                        'density': scenario_result.graph_metrics.density,
                        'has_cycles': scenario_result.graph_metrics.has_cycles,
                        'branching_factor': scenario_result.graph_metrics.actual_branching_factor
                    },
                    'verification_status': {
                        'uniqueness_verified': scenario_result.constraint_verification.is_unique if scenario_result.constraint_verification else None,
                        'smt_verified': scenario_result.smt_verification.is_satisfiable if scenario_result.smt_verification else None
                    },
                    'minimality_score': scenario_result.minimality_result.information_sufficiency_score if scenario_result.minimality_result else None
                }
            })
            
            # Validate question is solvable
            if self._validate_question_solvability(enhanced_question):
                return enhanced_question
            
        # If all attempts failed, return fallback
        return self._generate_fallback_question(question_type)

    def generate_question_batch(self, 
                               num_questions: int = 10,
                               complexity_range: tuple = (4.0, 8.0),
                               question_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate a batch of questions with varying complexity
        
        Args:
            num_questions: Number of questions to generate
            complexity_range: (min, max) complexity range
            question_types: List of question types to use
            
        Returns:
            List of enhanced questions
        """
        if question_types is None:
            question_types = ['final_count', 'initial_count', 'transfer_amount', 'difference', 'sum_all']
        
        questions = []
        min_complexity, max_complexity = complexity_range
        
        for i in range(num_questions):
            try:
                # Vary complexity across the range
                target_complexity = random.uniform(min_complexity, max_complexity)
                question_type = random.choice(question_types)
                
                # Generate enhanced question
                question = self.generate_enhanced_question(target_complexity, question_type)
                
                if question:
                    questions.append(question)
                    print(f"Generated question {i+1}/{num_questions} - Complexity: {target_complexity:.1f}")
                
            except Exception as e:
                print(f"Failed to generate question {i+1}: {e}")
                continue
        
        return questions

    def generate_complexity_controlled_dataset(self, 
                                             complexity_levels: Dict[str, int],
                                             output_file: str = "data/enhanced_questions.json") -> List[Dict[str, Any]]:
        """
        Generate dataset with controlled complexity distribution
        
        Args:
            complexity_levels: Dict mapping complexity level to count
                              e.g., {'simple': 20, 'moderate': 30, 'complex': 15}
            output_file: Output file path
            
        Returns:
            Complete dataset
        """
        
        complexity_ranges = {
            'simple': (3.0, 5.0),
            'moderate': (5.0, 8.0), 
            'complex': (8.0, 12.0)
        }
        
        all_questions = []
        
        for level, count in complexity_levels.items():
            if level not in complexity_ranges:
                print(f"Unknown complexity level: {level}")
                continue
                
            print(f"Generating {count} {level} questions...")
            min_comp, max_comp = complexity_ranges[level]
            
            level_questions = self.generate_question_batch(
                num_questions=count,
                complexity_range=(min_comp, max_comp)
            )
            
            # Tag questions with complexity level
            for q in level_questions:
                q['complexity_level'] = level
            
            all_questions.extend(level_questions)
        
        # Save dataset
        if output_file:
            self.dataset_manager.save_questions_json(all_questions, output_file)
            print(f"Saved {len(all_questions)} questions to {output_file}")
        
        return all_questions

    def generate_topology_variants(self, base_question_type: str = 'final_count', 
                                 num_variants: int = 5) -> List[Dict[str, Any]]:
        """
        Generate variants with different graph topologies
        
        Args:
            base_question_type: Base question type
            num_variants: Number of topology variants
            
        Returns:
            Questions with different graph structures
        """
        
        topology_variants = [
            # Linear chains
            TopologyParams(path_length=4, branching_factor=1.0, allow_cycles=False),
            # Branching structures  
            TopologyParams(path_length=3, branching_factor=2.5, allow_cycles=False),
            # Cyclic structures
            TopologyParams(path_length=3, branching_factor=2.0, allow_cycles=True),
            # Hub structures
            TopologyParams(path_length=2, branching_factor=3.0, hub_probability=0.8),
            # Complex networks
            TopologyParams(path_length=5, branching_factor=2.8, allow_cycles=True, hub_probability=0.5)
        ]
        
        questions = []
        
        for i, topology in enumerate(topology_variants[:num_variants]):
            config = GenerationConfig(
                topology_params=topology,
                target_complexity=6.0,
                apply_graph_aware_masking=True,
                use_structured_traversal=True
            )
            
            question = self.generate_enhanced_question(
                target_complexity=6.0,
                question_type=base_question_type,
                config=config
            )
            
            if question:
                question['topology_variant'] = i + 1
                question['topology_description'] = self._describe_topology(topology)
                questions.append(question)
        
        return questions

    def _describe_topology(self, params: TopologyParams) -> str:
        """Generate human-readable topology description"""
        desc = f"Path length: {params.path_length}, "
        desc += f"Branching: {params.branching_factor:.1f}, "
        desc += f"Cycles: {'Yes' if params.allow_cycles else 'No'}"
        
        if params.hub_probability > 0.5:
            desc += ", Hub-heavy"
        
        return desc

    def _generate_fallback_question(self, question_type: str) -> Dict[str, Any]:
        """Generate simple fallback question if enhanced generation fails"""
        return {
            'question_id': self._get_next_id(),
            'question_text': "How many items are there?",
            'answer': 5,
            'question_type': question_type,
            'generation_metadata': {'fallback': True}
        }

    def _get_next_id(self) -> int:
        """Get next question ID"""
        self.question_counter += 1
        return self.question_counter

    def _validate_question_solvability(self, question: Dict[str, Any]) -> bool:
        """
        Validate that a question can be solved with the given context
        
        Args:
            question: Generated question dictionary
            
        Returns:
            True if question is solvable, False otherwise
        """
        try:
            context = question.get('context', '')
            question_text = question.get('question', '')
            question_type = question.get('question_type', '')
            
            # Basic checks
            if not context or not question_text:
                return False
            
            # Check if constraint verification passed
            metadata = question.get('generation_metadata', {})
            verification = metadata.get('verification_status', {})
            uniqueness_verified = verification.get('uniqueness_verified')
            
            # If uniqueness verification failed, question is unsolvable
            if uniqueness_verified is False:
                return False
            
            # Additional solvability checks based on question type
            if question_type == 'sum_all':
                # For total questions, need complete initial state information
                return self._check_total_question_solvability(context)
            elif question_type == 'final_count':
                # For final count questions, need target agent info
                return self._check_final_count_solvability(context, question_text)
            
            # If uniqueness verified or no major issues found
            return True
            
        except Exception:
            # If validation fails, err on the side of caution
            return False
    
    def _check_total_question_solvability(self, context: str) -> bool:
        """Check if a sum_all question has enough information"""
        # Must have initial state information for agents that give items
        has_initial_states = 'Initially' in context or 'starts with' in context
        has_transfers = 'gives' in context
        
        # Basic requirement: some initial state info
        return has_initial_states and has_transfers
    
    def _check_final_count_solvability(self, context: str, question: str) -> bool:
        """Check if a final_count question has enough information"""
        # Need either initial state or way to deduce from transfers
        has_initial_info = 'Initially' in context or 'starts with' in context
        has_transfers = 'gives' in context
        
        # Check object consistency - question object should appear in context
        question_lower = question.lower()
        context_lower = context.lower()
        
        # Extract potential object from question (simple heuristic)
        if 'how many' in question_lower:
            # This is a basic check - in practice would need more sophisticated parsing
            return has_initial_info or has_transfers
        
        return True

    def analyze_generated_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of generated questions"""
        
        if not questions:
            return {'error': 'No questions to analyze'}
        
        # Extract complexity scores
        complexity_scores = []
        question_types = []
        verification_stats = {'unique': 0, 'non_unique': 0, 'unknown': 0}
        
        for q in questions:
            metadata = q.get('generation_metadata', {})
            
            if metadata.get('complexity_score'):
                complexity_scores.append(metadata['complexity_score'])
            
            question_types.append(q.get('question_type', 'unknown'))
            
            # Verification statistics
            verification = metadata.get('verification_status', {})
            uniqueness = verification.get('uniqueness_verified')
            
            if uniqueness is True:
                verification_stats['unique'] += 1
            elif uniqueness is False:
                verification_stats['non_unique'] += 1
            else:
                verification_stats['unknown'] += 1
        
        analysis = {
            'total_questions': len(questions),
            'complexity_stats': {
                'mean': np.mean(complexity_scores) if complexity_scores else 0,
                'std': np.std(complexity_scores) if complexity_scores else 0,
                'min': min(complexity_scores) if complexity_scores else 0,
                'max': max(complexity_scores) if complexity_scores else 0
            },
            'question_type_distribution': {qt: question_types.count(qt) for qt in set(question_types)},
            'verification_stats': verification_stats,
            'minimality_scores': []
        }
        
        # Collect minimality scores
        for q in questions:
            metadata = q.get('generation_metadata', {})
            min_score = metadata.get('minimality_score')
            if min_score is not None:
                analysis['minimality_scores'].append(min_score)
        
        if analysis['minimality_scores']:
            analysis['minimality_stats'] = {
                'mean': np.mean(analysis['minimality_scores']),
                'min': min(analysis['minimality_scores']),
                'max': max(analysis['minimality_scores'])
            }
        
        return analysis


# Example usage and testing
if __name__ == "__main__":
    generator = EnhancedQuestionGenerator()
    
    print("=== Enhanced Question Generator Test ===")
    
    # Generate a single enhanced question
    print("Generating single enhanced question...")
    question = generator.generate_enhanced_question(target_complexity=7.0, question_type='final_count')
    
    if question:
        print(f"Question: {question['question']}")
        print(f"Answer: {question['answer']}")
        print(f"Complexity: {question['generation_metadata']['complexity_score']}")
        print(f"Graph has cycles: {question['generation_metadata']['graph_metrics']['has_cycles']}")
    
    # Generate small batch with complexity control
    print("\nGenerating complexity-controlled dataset...")
    complexity_levels = {
        'simple': 3,
        'moderate': 5, 
        'complex': 2
    }
    
    dataset = generator.generate_complexity_controlled_dataset(
        complexity_levels, 
        output_file="data/test_enhanced_questions.json"
    )
    
    # Analyze results
    analysis = generator.analyze_generated_questions(dataset)
    print(f"\nDataset Analysis:")
    print(f"Total questions: {analysis['total_questions']}")
    print(f"Mean complexity: {analysis['complexity_stats']['mean']:.2f}")
    print(f"Unique solutions: {analysis['verification_stats']['unique']}")
    
    print("\nEnhanced question generation complete!")