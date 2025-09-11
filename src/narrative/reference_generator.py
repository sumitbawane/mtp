"""
Anaphoric Reference Generator for Natural Language Flow
Generates "those apples" type references for items traversing paths
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scenario_core import Transfer, Agent, Scenario
from .traversal_planner import TraversalPlan, NarrativeNode


@dataclass
class ReferenceContext:
    """Context for anaphoric reference resolution"""
    object_type: str
    current_agent: str
    previous_mentions: List[str]  # Previous ways this object was referenced
    path_position: int  # Position in the transfer path
    total_path_length: int
    quantity: int


@dataclass
class Reference:
    """Generated anaphoric reference"""
    original_text: str
    reference_text: str
    reference_type: str  # 'definite', 'demonstrative', 'pronoun', 'ellipsis'
    confidence: float


class AnaphoricReferenceGenerator:
    """Generates natural anaphoric references for object tracking"""
    
    def __init__(self):
        # Reference patterns for different contexts
        self.definite_patterns = [
            "the {object_type}s",
            "the {quantity} {object_type}s", 
            "the same {object_type}s"
        ]
        
        self.demonstrative_patterns = [
            "those {object_type}s",
            "these {object_type}s",
            "that batch of {object_type}s",
            "those same {object_type}s"
        ]
        
        self.pronoun_patterns = [
            "them",
            "those",
            "these"
        ]
        
        # Quantity-specific patterns
        self.quantity_references = {
            1: ["it", "that one", "the item"],
            2: ["them", "both", "the pair", "those two"],
            3: ["them", "all three", "the trio"], 
            4: ["them", "all four", "the set"],
            5: ["them", "all five", "the bunch"]
        }
        
        # Context-based selection weights
        self.pattern_weights = {
            'first_mention': {'definite': 0.8, 'demonstrative': 0.2, 'pronoun': 0.0},
            'middle_path': {'definite': 0.3, 'demonstrative': 0.5, 'pronoun': 0.2},
            'final_mention': {'definite': 0.2, 'demonstrative': 0.3, 'pronoun': 0.5},
            'short_distance': {'definite': 0.4, 'demonstrative': 0.4, 'pronoun': 0.2},
            'long_distance': {'definite': 0.6, 'demonstrative': 0.3, 'pronoun': 0.1}
        }
    
    def generate_references(self, traversal_plan: TraversalPlan, 
                          scenario: Scenario) -> Dict[str, str]:
        """
        Generate anaphoric references for the entire traversal plan
        
        Args:
            traversal_plan: Complete traversal plan
            scenario: AWP scenario
            
        Returns:
            Dict mapping original text to reference text
        """
        
        references = {}
        
        # Track object mentions through the narrative
        object_contexts = self._build_object_contexts(traversal_plan, scenario)
        
        # Generate references for each narrative node
        for node in traversal_plan.narrative_nodes:
            if node.node_type == 'transfer':
                node_refs = self._generate_node_references(node, object_contexts)
                references.update(node_refs)
        
        return references
    
    def _build_object_contexts(self, traversal_plan: TraversalPlan, 
                             scenario: Scenario) -> Dict[str, List[ReferenceContext]]:
        """Build context tracking for each object type through the narrative"""
        
        contexts = defaultdict(list)
        
        # Process each transfer in order to build contexts
        for i, transfer in enumerate(traversal_plan.transfer_sequence_order):
            obj_type = transfer.object_type
            
            # Find previous mentions of this object type
            previous_mentions = []
            for prev_transfer in traversal_plan.transfer_sequence_order[:i]:
                if prev_transfer.object_type == obj_type:
                    previous_mentions.append(f"{prev_transfer.from_agent}_{prev_transfer.to_agent}")
            
            # Calculate path position for this object
            obj_transfers = [t for t in traversal_plan.transfer_sequence_order if t.object_type == obj_type]
            path_position = next((j for j, t in enumerate(obj_transfers) if t.transfer_id == transfer.transfer_id), 0)
            
            context = ReferenceContext(
                object_type=obj_type,
                current_agent=transfer.from_agent,
                previous_mentions=previous_mentions,
                path_position=path_position,
                total_path_length=len(obj_transfers),
                quantity=transfer.quantity
            )
            
            contexts[transfer.object_type].append(context)
        
        return contexts
    
    def _generate_node_references(self, node: NarrativeNode, 
                                object_contexts: Dict[str, List[ReferenceContext]]) -> Dict[str, str]:
        """Generate references for a specific narrative node"""
        
        references = {}
        content = node.content
        
        # Extract transfer information from node content
        transfer_match = re.search(r'(\w+) gives (\d+) (\w+)s? to (\w+)', content)
        if not transfer_match:
            return references
        
        from_agent, quantity_str, obj_type, to_agent = transfer_match.groups()
        quantity = int(quantity_str)
        
        # Find relevant context
        relevant_contexts = object_contexts.get(obj_type, [])
        if not relevant_contexts:
            return references
        
        # Find the context for this specific transfer
        context = None
        for ctx in relevant_contexts:
            if ctx.current_agent == from_agent and ctx.quantity == quantity:
                context = ctx
                break
        
        if not context:
            return references
        
        # Generate appropriate reference
        reference = self._select_best_reference(context)
        
        if reference and reference.reference_text != f"{quantity} {obj_type}{'s' if quantity != 1 else ''}":
            # Replace the object phrase in the original text
            original_phrase = f"{quantity} {obj_type}{'s' if quantity != 1 else ''}"
            new_content = content.replace(original_phrase, reference.reference_text)
            references[content] = new_content
        
        return references
    
    def _select_best_reference(self, context: ReferenceContext) -> Optional[Reference]:
        """Select the best anaphoric reference for given context"""
        
        # Determine context type for weight selection
        context_type = self._classify_context(context)
        weights = self.pattern_weights.get(context_type, self.pattern_weights['middle_path'])
        
        # Select reference type based on weights and context
        if context.path_position == 0:
            # First mention - usually use definite article
            return self._generate_definite_reference(context)
        elif context.path_position == context.total_path_length - 1:
            # Final mention - can use pronouns
            return self._generate_pronoun_reference(context)
        else:
            # Middle of path - prefer demonstratives
            return self._generate_demonstrative_reference(context)
    
    def _classify_context(self, context: ReferenceContext) -> str:
        """Classify context for reference selection"""
        
        if context.path_position == 0:
            return 'first_mention'
        elif context.path_position == context.total_path_length - 1:
            return 'final_mention'
        elif len(context.previous_mentions) <= 1:
            return 'short_distance'
        else:
            return 'long_distance'
    
    def _generate_definite_reference(self, context: ReferenceContext) -> Reference:
        """Generate definite article reference"""
        
        if context.quantity == 1:
            reference_text = f"the {context.object_type}"
        else:
            reference_text = f"the {context.quantity} {context.object_type}s"
        
        return Reference(
            original_text=f"{context.quantity} {context.object_type}{'s' if context.quantity != 1 else ''}",
            reference_text=reference_text,
            reference_type="definite",
            confidence=0.8
        )
    
    def _generate_demonstrative_reference(self, context: ReferenceContext) -> Reference:
        """Generate demonstrative reference (those, these)"""
        
        if context.quantity == 1:
            reference_text = f"that {context.object_type}"
        elif context.quantity <= 5:
            if context.path_position > 1:
                reference_text = f"those {context.object_type}s"
            else:
                reference_text = f"these {context.object_type}s"
        else:
            reference_text = f"those {context.object_type}s"
        
        return Reference(
            original_text=f"{context.quantity} {context.object_type}{'s' if context.quantity != 1 else ''}",
            reference_text=reference_text,
            reference_type="demonstrative", 
            confidence=0.9
        )
    
    def _generate_pronoun_reference(self, context: ReferenceContext) -> Reference:
        """Generate pronoun reference"""
        
        if context.quantity == 1:
            reference_text = "it"
        elif context.quantity in self.quantity_references:
            options = self.quantity_references[context.quantity]
            reference_text = options[0]  # Select first option
        else:
            reference_text = "them"
        
        return Reference(
            original_text=f"{context.quantity} {context.object_type}{'s' if context.quantity != 1 else ''}",
            reference_text=reference_text,
            reference_type="pronoun",
            confidence=0.7
        )
    
    def apply_references_to_plan(self, traversal_plan: TraversalPlan,
                               scenario: Scenario) -> TraversalPlan:
        """Apply anaphoric references to the traversal plan"""
        
        references = self.generate_references(traversal_plan, scenario)
        
        # Create new plan with references applied
        updated_nodes = []
        for node in traversal_plan.narrative_nodes:
            updated_content = node.content
            
            # Apply any references for this node
            if node.content in references:
                updated_content = references[node.content]
            
            updated_node = NarrativeNode(
                node_id=node.node_id,
                node_type=node.node_type,
                content=updated_content,
                dependencies=node.dependencies,
                priority=node.priority
            )
            updated_nodes.append(updated_node)
        
        # Return updated plan
        return TraversalPlan(
            agent_introduction_order=traversal_plan.agent_introduction_order,
            transfer_sequence_order=traversal_plan.transfer_sequence_order,
            narrative_nodes=updated_nodes,
            reference_chains=traversal_plan.reference_chains,
            story_structure=traversal_plan.story_structure
        )
    
    def generate_story_text(self, traversal_plan: TraversalPlan) -> str:
        """Generate complete story text from traversal plan"""
        
        # Sort nodes by dependencies and priority
        sorted_nodes = self._topological_sort_nodes(traversal_plan.narrative_nodes)
        
        # Generate story text
        story_sentences = []
        for node in sorted_nodes:
            if node.content.strip():
                story_sentences.append(node.content.strip())
        
        return ' '.join(story_sentences)
    
    def _topological_sort_nodes(self, nodes: List[NarrativeNode]) -> List[NarrativeNode]:
        """Sort nodes in dependency order"""
        
        # Simple dependency resolution - can be made more sophisticated
        node_map = {node.node_id: node for node in nodes}
        
        # Separate intro nodes and transfer nodes
        intro_nodes = [n for n in nodes if n.node_type == 'agent_intro']
        transfer_nodes = [n for n in nodes if n.node_type == 'transfer']
        
        # Sort intro nodes by priority
        intro_nodes.sort(key=lambda n: n.priority)
        
        # Sort transfer nodes by dependencies and priority  
        transfer_nodes.sort(key=lambda n: (len(n.dependencies), n.priority))
        
        return intro_nodes + transfer_nodes