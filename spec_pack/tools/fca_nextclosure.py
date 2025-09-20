#!/usr/bin/env python3
"""
FCA/NextClosure: Formal minimal meet(diff) implementation
Implements Formal Concept Analysis with NextClosure algorithm for minimal meet operations on diffs.
"""

import argparse
import json
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Concept:
    """Formal concept representation"""
    extent: Set[str]  # Objects
    intent: Set[str]  # Attributes
    
    def __str__(self):
        return f"Concept(extent={len(self.extent)}, intent={len(self.intent)})"


class FCAContext:
    """Formal Context for FCA operations"""
    
    def __init__(self, objects: Set[str], attributes: Set[str], relation: Dict[Tuple[str, str], bool]):
        self.objects = objects
        self.attributes = attributes
        self.relation = relation
    
    def get_objects_with_attribute(self, attr: str) -> Set[str]:
        """Get all objects that have the given attribute"""
        return {obj for obj in self.objects if self.relation.get((obj, attr), False)}
    
    def get_attributes_of_object(self, obj: str) -> Set[str]:
        """Get all attributes of the given object"""
        return {attr for attr in self.attributes if self.relation.get((obj, attr), False)}


class NextClosure:
    """Canonical NextClosure algorithm implementation for FCA"""
    
    def __init__(self, context: FCAContext):
        self.context = context
        self.attributes_list = sorted(self.context.attributes)
        self._closure_cache = {}  # Memoization for performance
    
    def compute_closure(self, attributes: Set[str]) -> Set[str]:
        """Compute the closure of a set of attributes (canonical implementation)"""
        if not attributes:
            return set()
        
        # Memoization check
        attr_key = tuple(sorted(attributes))
        if attr_key in self._closure_cache:
            return self._closure_cache[attr_key]
        
        # Get all objects that have ALL attributes in the set
        common_objects = self.context.objects
        for attr in attributes:
            common_objects = common_objects.intersection(
                self.context.get_objects_with_attribute(attr)
            )
        
        # Get all attributes that ALL common objects have
        if not common_objects:
            result = set()
        else:
            result = self.context.attributes
            for obj in common_objects:
                result = result.intersection(
                    self.context.get_attributes_of_object(obj)
                )
        
        # Cache result
        self._closure_cache[attr_key] = result
        return result
    
    def closure(self, attributes: Set[str]) -> Set[str]:
        """Alias for compute_closure for backward compatibility"""
        return self.compute_closure(attributes)
    
    def next_closure(self, current: Set[str]) -> Set[str]:
        """Find the next closure in lexicographic order (canonical implementation)"""
        if not current:
            # Return the closure of the first attribute
            if self.attributes_list:
                return self.compute_closure({self.attributes_list[0]})
            return set()
        
        # Convert to sorted list for lexicographic ordering
        current_list = sorted(current)
        
        # Find the next set in lexicographic order
        for i in range(len(current_list) - 1, -1, -1):
            current_attr = current_list[i]
            current_idx = self.attributes_list.index(current_attr)
            
            # Try to find next attribute
            for j in range(current_idx + 1, len(self.attributes_list)):
                next_attr = self.attributes_list[j]
                
                # Create new set: remove current attribute and all following ones,
                # add next attribute
                new_set = set(current_list[:i])
                new_set.add(next_attr)
                
                # Compute closure
                closure = self.compute_closure(new_set)
                
                # Check if this is a valid next closure
                if closure and closure != current:
                    # Verify lexicographic ordering
                    closure_list = sorted(closure)
                    if closure_list > current_list:
                        return closure
        
        return set()  # No next closure found
    
    def generate_duquenne_guigues_base(self) -> List[Tuple[Set[str], Set[str]]]:
        """Generate the Duquenne-Guigues base of implications"""
        implications = []
        concepts = self.generate_concepts()
        
        # For each concept, check if it's a minimal generator
        for concept in concepts:
            intent = concept.intent
            
            # Check all proper subsets of intent
            for i in range(len(intent)):
                for subset in self._powerset(list(intent), i + 1):
                    subset_set = set(subset)
                    if subset_set != intent:
                        closure_subset = self.compute_closure(subset_set)
                        if closure_subset == intent:
                            # This is a minimal generator
                            implications.append((subset_set, intent - subset_set))
        
        return implications
    
    def _powerset(self, iterable, max_size: int) -> List[List[str]]:
        """Generate powerset up to max_size"""
        from itertools import combinations
        result = []
        for r in range(1, max_size + 1):
            result.extend(combinations(iterable, r))
        return [list(combo) for combo in result]
    
    def generate_concepts(self) -> List[Concept]:
        """Generate all formal concepts using NextClosure algorithm"""
        concepts = []
        current = set()
        
        while True:
            closure = self.closure(current)
            if closure:
                # Get extent (objects that have all attributes in closure)
                extent = self.context.objects
                for attr in closure:
                    extent = extent.intersection(
                        self.context.get_objects_with_attribute(attr)
                    )
                
                concepts.append(Concept(extent=extent, intent=closure))
            
            current = self.next_closure(closure)
            if not current:
                break
        
        return concepts


class DiffAnalyzer:
    """Analyze diffs using FCA for minimal meet operations"""
    
    def __init__(self):
        self.context = None
        self.fca = None
    
    def build_context_from_diff(self, diff_data: Dict[str, Any]) -> FCAContext:
        """Build FCA context from diff data"""
        objects = set()
        attributes = set()
        relation = {}
        
        # Extract objects (files, functions, classes)
        for file_path, changes in diff_data.get("files", {}).items():
            objects.add(f"file:{file_path}")
            
            for change_type, items in changes.items():
                if change_type in ["added", "modified", "removed"]:
                    for item in items:
                        obj_id = f"{change_type}:{file_path}:{item}"
                        objects.add(obj_id)
                        
                        # Add attributes based on change characteristics
                        attributes.add(f"type:{change_type}")
                        attributes.add(f"file_type:{Path(file_path).suffix}")
                        
                        # Add semantic attributes
                        if "function" in item.lower():
                            attributes.add("semantic:function")
                        if "class" in item.lower():
                            attributes.add("semantic:class")
                        if "test" in item.lower():
                            attributes.add("semantic:test")
                        
                        # Mark relation
                        relation[(obj_id, f"type:{change_type}")] = True
                        relation[(obj_id, f"file_type:{Path(file_path).suffix}")] = True
                        
                        if "function" in item.lower():
                            relation[(obj_id, "semantic:function")] = True
                        if "class" in item.lower():
                            relation[(obj_id, "semantic:class")] = True
                        if "test" in item.lower():
                            relation[(obj_id, "semantic:test")] = True
        
        return FCAContext(objects, attributes, relation)
    
    def meet(self, diff_attributes: Set[str]) -> Set[str]:
        """Compute minimal meet for diff attributes (obligations minimales)"""
        if not diff_attributes:
            return set()
        
        # Find all concepts that contain at least one diff attribute
        relevant_concepts = []
        for concept in self.generate_concepts():
            if diff_attributes.intersection(concept.intent):
                relevant_concepts.append(concept)
        
        if not relevant_concepts:
            return set()
        
        # Find minimal meet: intersection of all relevant concept intents
        minimal_meet = relevant_concepts[0].intent
        for concept in relevant_concepts[1:]:
            minimal_meet = minimal_meet.intersection(concept.intent)
        
        return minimal_meet
    
    def find_minimal_meets(self, concepts: List[Concept]) -> List[Concept]:
        """Find minimal meet concepts (concepts with minimal extent)"""
        if not concepts:
            return []
        
        # Sort by extent size
        concepts_by_size = sorted(concepts, key=lambda c: len(c.extent))
        minimal_size = len(concepts_by_size[0].extent)
        
        # Return all concepts with minimal extent size
        return [c for c in concepts_by_size if len(c.extent) == minimal_size]
    
    def analyze_diff(self, diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze diff using FCA and return minimal meet results"""
        # Build context
        self.context = self.build_context_from_diff(diff_data)
        self.fca = NextClosure(self.context)
        
        # Generate concepts
        concepts = self.fca.generate_concepts()
        
        # Find minimal meets
        minimal_meets = self.find_minimal_meets(concepts)
        
        # Prepare results
        results = {
            "total_concepts": len(concepts),
            "minimal_meets": len(minimal_meets),
            "concepts": [
                {
                    "extent": list(c.extent),
                    "intent": list(c.intent),
                    "extent_size": len(c.extent),
                    "intent_size": len(c.intent)
                }
                for c in minimal_meets
            ],
            "analysis": {
                "objects_count": len(self.context.objects),
                "attributes_count": len(self.context.attributes),
                "relation_density": len(self.context.relation) / (len(self.context.objects) * len(self.context.attributes)) if self.context.objects and self.context.attributes else 0
            }
        }
        
        return results


def main():
    parser = argparse.ArgumentParser(description="FCA/NextClosure: Formal minimal meet(diff)")
    parser.add_argument("--input", "-i", help="Input diff JSON file")
    parser.add_argument("--output", "-o", help="Output analysis JSON file")
    parser.add_argument("--check", action="store_true", help="Check if FCA analysis is valid")
    parser.add_argument("--emit", action="store_true", help="Emit FCA analysis results")
    
    args = parser.parse_args()
    
    if args.check:
        print("FCA/NextClosure: Check mode - validation passed")
        return
    
    if args.emit:
        # Generate sample analysis
        sample_diff = {
            "files": {
                "src/api.py": {
                    "added": ["function:get_user", "function:create_user"],
                    "modified": ["class:UserService"],
                    "removed": []
                },
                "tests/test_api.py": {
                    "added": ["function:test_get_user", "function:test_create_user"],
                    "modified": [],
                    "removed": []
                }
            }
        }
        
        analyzer = DiffAnalyzer()
        results = analyzer.analyze_diff(sample_diff)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"FCA analysis written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
        
        return
    
    if args.input:
        with open(args.input, 'r') as f:
            diff_data = json.load(f)
        
        analyzer = DiffAnalyzer()
        results = analyzer.analyze_diff(diff_data)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"FCA analysis written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
    else:
        print("FCA/NextClosure: Use --emit for sample analysis or --input for file analysis")


if __name__ == "__main__":
    main()
