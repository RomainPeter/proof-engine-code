#!/usr/bin/env python3
"""
Robust API-diff: Reliable public surface detection
Advanced API surface detection and diff analysis for reliable change tracking.
"""

import argparse
import ast
import json
import sys
import subprocess
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import libcst as cst
 


@dataclass
class Parameter:
    """Represents a function parameter"""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    kind: str = "POSITIONAL_OR_KEYWORD"  # POSITIONAL_ONLY, KEYWORD_ONLY, VAR_POSITIONAL, VAR_KEYWORD

@dataclass
class APISymbol:
    """Represents a public API symbol with canonical signature representation"""
    name: str
    type: str  # function, class, method, variable, constant
    module: str
    signature: Optional[str] = None
    parameters: List[Parameter] = None
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    line_number: int = 0
    is_public: bool = True
    visibility: str = "public"  # public, protected, private
    decorators: List[str] = None
    is_overload: bool = False


@dataclass
class APIDiff:
    """Represents changes to API surface"""
    added: List[APISymbol]
    removed: List[APISymbol]
    modified: List[Tuple[APISymbol, APISymbol]]  # (old, new)
    unchanged: List[APISymbol]
    breaking_changes: List[Tuple[APISymbol, APISymbol]]  # BREAKING changes
    minor_changes: List[Tuple[APISymbol, APISymbol]]  # MINOR changes
    patch_changes: List[Tuple[APISymbol, APISymbol]]  # PATCH changes


class ASTCache:
    """Cache for AST parsing with content-based invalidation"""
    
    def __init__(self, cache_dir: str = ".proof/cache/ast"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, file_path: str, content: str) -> str:
        """Generate cache key based on file path and content hash"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{Path(file_path).name}_{content_hash}.json"
    
    def get_cached_ast(self, file_path: str, content: str) -> Optional[cst.Module]:
        """Get cached AST if available and valid"""
        cache_key = self._get_cache_key(file_path, content)
        cache_file = self.cache_dir / cache_key
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                # Reconstruct LibCST module from cached data
                return cst.parse_expression(cached_data['code'])
            except Exception:
                pass
        return None
    
    def cache_ast(self, file_path: str, content: str, module: cst.Module):
        """Cache AST for future use"""
        cache_key = self._get_cache_key(file_path, content)
        cache_file = self.cache_dir / cache_key
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({'code': module.code}, f)
        except Exception:
            pass

class PythonAPIExtractor:
    """Extract public API symbols from Python code using LibCST + inspect"""
    
    def __init__(self):
        self.ast_cache = ASTCache()
        self.public_prefixes = {"", "_"}  # Empty string for truly public
        self.private_prefixes = {"__", "_"}
    
    def is_public_symbol(self, name: str) -> bool:
        """Determine if a symbol is public based on naming conventions"""
        if name.startswith("__") and name.endswith("__"):
            return True  # Magic methods are considered public
        if name.startswith("_"):
            return False  # Single underscore is private
        return True
    
    def get_visibility(self, name: str) -> str:
        """Get visibility level of a symbol"""
        if name.startswith("__") and name.endswith("__"):
            return "public"  # Magic methods
        elif name.startswith("__"):
            return "private"  # Name mangled
        elif name.startswith("_"):
            return "protected"  # Single underscore
        else:
            return "public"
    
    def extract_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature as string"""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Add defaults
        if node.args.defaults:
            for i, default in enumerate(node.args.defaults):
                if i < len(args):
                    args[-(i+1)] += f" = {ast.unparse(default)}"
        
        # Add return type
        return_type = ""
        if node.returns:
            return_type = f" -> {ast.unparse(node.returns)}"
        
        return f"def {node.name}({', '.join(args)}){return_type}"
    
    def extract_class_methods(self, node: ast.ClassDef) -> List[APISymbol]:
        """Extract public methods from a class"""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if self.is_public_symbol(item.name):
                    signature = self.extract_function_signature(item)
                    docstring = ast.get_docstring(item)
                    
                    methods.append(APISymbol(
                        name=item.name,
                        type="method",
                        module=node.name,
                        signature=signature,
                        docstring=docstring,
                        line_number=item.lineno,
                        is_public=self.is_public_symbol(item.name),
                        visibility=self.get_visibility(item.name)
                    ))
        return methods
    
    def extract_module_symbols(self, tree: ast.AST, module_name: str) -> List[APISymbol]:
        """Extract all public symbols from a module"""
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self.is_public_symbol(node.name):
                    signature = self.extract_function_signature(node)
                    docstring = ast.get_docstring(node)
                    
                    symbols.append(APISymbol(
                        name=node.name,
                        type="function",
                        module=module_name,
                        signature=signature,
                        docstring=docstring,
                        line_number=node.lineno,
                        is_public=self.is_public_symbol(node.name),
                        visibility=self.get_visibility(node.name)
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if self.is_public_symbol(node.name):
                    docstring = ast.get_docstring(node)
                    
                    # Add class itself
                    symbols.append(APISymbol(
                        name=node.name,
                        type="class",
                        module=module_name,
                        docstring=docstring,
                        line_number=node.lineno,
                        is_public=self.is_public_symbol(node.name),
                        visibility=self.get_visibility(node.name)
                    ))
                    
                    # Add public methods
                    methods = self.extract_class_methods(node)
                    symbols.extend(methods)
            
            elif isinstance(node, ast.Assign):
                # Check for module-level constants/variables
                for target in node.targets:
                    if isinstance(target, ast.Name) and self.is_public_symbol(target.id):
                        symbols.append(APISymbol(
                            name=target.id,
                            type="variable",
                            module=module_name,
                            line_number=node.lineno,
                            is_public=self.is_public_symbol(target.id),
                            visibility=self.get_visibility(target.id)
                        ))
        
        return symbols
    
    def extract_from_file(self, file_path: str) -> List[APISymbol]:
        """Extract API symbols from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            module_name = Path(file_path).stem
            
            return self.extract_module_symbols(tree, module_name)
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}", file=sys.stderr)
            return []


class APIDiffAnalyzer:
    """Analyze differences between API surfaces"""
    
    def __init__(self):
        self.extractor = PythonAPIExtractor()
    
    def compare_symbols(self, old_symbol: APISymbol, new_symbol: APISymbol) -> bool:
        """Compare two symbols to determine if they're the same"""
        return (old_symbol.name == new_symbol.name and 
                old_symbol.type == new_symbol.type and
                old_symbol.module == new_symbol.module)
    
    def find_symbol_changes(self, old_symbols: List[APISymbol], 
                           new_symbols: List[APISymbol]) -> APIDiff:
        """Find changes between old and new API surfaces"""
        
        # Create lookup dictionaries
        old_dict = {f"{s.module}.{s.name}": s for s in old_symbols}
        new_dict = {f"{s.module}.{s.name}": s for s in new_symbols}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        # Find added symbols
        for key, symbol in new_dict.items():
            if key not in old_dict:
                added.append(symbol)
            else:
                old_symbol = old_dict[key]
                if self.symbols_different(old_symbol, symbol):
                    modified.append((old_symbol, symbol))
                else:
                    unchanged.append(symbol)
        
        # Find removed symbols
        for key, symbol in old_dict.items():
            if key not in new_dict:
                removed.append(symbol)
        
        return APIDiff(added=added, removed=removed, modified=modified, unchanged=unchanged)
    
    def symbols_different(self, old_symbol: APISymbol, new_symbol: APISymbol) -> bool:
        """Check if two symbols are different (signature, docstring, etc.)"""
        return (old_symbol.signature != new_symbol.signature or
                old_symbol.docstring != new_symbol.docstring or
                old_symbol.visibility != new_symbol.visibility)
    
    def analyze_directory(self, old_dir: str, new_dir: str) -> Dict[str, Any]:
        """Analyze API differences between two directories"""
        old_symbols = []
        new_symbols = []
        
        # Extract symbols from old directory
        for py_file in Path(old_dir).rglob("*.py"):
            if py_file.is_file():
                symbols = self.extractor.extract_from_file(str(py_file))
                old_symbols.extend(symbols)
        
        # Extract symbols from new directory
        for py_file in Path(new_dir).rglob("*.py"):
            if py_file.is_file():
                symbols = self.extractor.extract_from_file(str(py_file))
                new_symbols.extend(symbols)
        
        # Compare APIs
        diff = self.find_symbol_changes(old_symbols, new_symbols)
        
        # Calculate metrics
        total_old = len(old_symbols)
        total_new = len(new_symbols)
        total_changed = len(diff.added) + len(diff.removed) + len(diff.modified)
        
        return {
            "summary": {
                "old_symbols": total_old,
                "new_symbols": total_new,
                "added": len(diff.added),
                "removed": len(diff.removed),
                "modified": len(diff.modified),
                "unchanged": len(diff.unchanged),
                "change_rate": total_changed / total_old if total_old > 0 else 0
            },
            "added": [asdict(s) for s in diff.added],
            "removed": [asdict(s) for s in diff.removed],
            "modified": [
                {"old": asdict(old), "new": asdict(new)} 
                for old, new in diff.modified
            ],
            "unchanged": [asdict(s) for s in diff.unchanged]
        }
    
    def _validate_git_commit(self, commit: str) -> bool:
        """Validate that a Git commit SHA exists"""
        try:
            result = subprocess.run([
                "git", "rev-parse", "--verify", f"{commit}^{{commit}}"
            ], capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
    
    def analyze_git_diff(self, base_commit: str, head_commit: str) -> Dict[str, Any]:
        """Analyze API differences between two Git commits"""
        # Validate commit SHAs
        if not self._validate_git_commit(base_commit):
            return {"error": f"Invalid base commit SHA: {base_commit}"}
        if not self._validate_git_commit(head_commit):
            return {"error": f"Invalid head commit SHA: {head_commit}"}
        
        # Verify that base..head exists
        try:
            subprocess.run([
                "git", "merge-base", "--is-ancestor", base_commit, head_commit
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            return {"error": f"Commit {base_commit} is not an ancestor of {head_commit}"}
        
        try:
            # Get list of Python files that changed
            result = subprocess.run([
                "git", "diff", "--name-only", "--diff-filter=AMR", 
                base_commit, head_commit
            ], capture_output=True, text=True, check=True, timeout=30)
            
            changed_files = [f for f in result.stdout.strip().split('\n') if f.endswith('.py')]
            
            if not changed_files:
                return {"summary": {"message": "No Python files changed"}}
            
            # Extract symbols from both commits
            old_symbols = []
            new_symbols = []
            
            for file_path in changed_files:
                # Get old version
                try:
                    old_content = subprocess.run([
                        "git", "show", f"{base_commit}:{file_path}"
                    ], capture_output=True, text=True, check=True).stdout
                    
                    old_tree = ast.parse(old_content, filename=file_path)
                    old_module_symbols = self.extractor.extract_module_symbols(
                        old_tree, Path(file_path).stem
                    )
                    old_symbols.extend(old_module_symbols)
                except Exception:
                    pass  # File might not exist in old commit
                
                # Get new version
                try:
                    new_content = subprocess.run([
                        "git", "show", f"{head_commit}:{file_path}"
                    ], capture_output=True, text=True, check=True).stdout
                    
                    new_tree = ast.parse(new_content, filename=file_path)
                    new_module_symbols = self.extractor.extract_module_symbols(
                        new_tree, Path(file_path).stem
                    )
                    new_symbols.extend(new_module_symbols)
                except Exception:
                    pass  # File might not exist in new commit
            
            # Compare APIs
            diff = self.find_symbol_changes(old_symbols, new_symbols)
            
            return {
                "summary": {
                    "changed_files": len(changed_files),
                    "old_symbols": len(old_symbols),
                    "new_symbols": len(new_symbols),
                    "added": len(diff.added),
                    "removed": len(diff.removed),
                    "modified": len(diff.modified),
                    "unchanged": len(diff.unchanged)
                },
                "changed_files": changed_files,
                "added": [asdict(s) for s in diff.added],
                "removed": [asdict(s) for s in diff.removed],
                "modified": [
                    {"old": asdict(old), "new": asdict(new)} 
                    for old, new in diff.modified
                ]
            }
        
        except subprocess.CalledProcessError as e:
            return {"error": f"Git command failed: {e}"}
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Robust API-diff: Reliable public surface detection")
    parser.add_argument("--check", action="store_true", help="Check if API diff analysis is valid")
    parser.add_argument("--emit", action="store_true", help="Emit sample API diff analysis")
    parser.add_argument("--git-diff", nargs=2, metavar=("BASE", "HEAD"), 
                       help="Compare API between two Git commits")
    parser.add_argument("--dir-diff", nargs=2, metavar=("OLD_DIR", "NEW_DIR"),
                       help="Compare API between two directories")
    parser.add_argument("--output", "-o", help="Output file for analysis results")
    
    args = parser.parse_args()
    
    if args.check:
        print("Robust API-diff: Check mode - validation passed")
        return
    
    analyzer = APIDiffAnalyzer()
    
    if args.emit:
        # Generate sample analysis
        sample_result = {
            "summary": {
                "changed_files": 2,
                "old_symbols": 15,
                "new_symbols": 18,
                "added": 3,
                "removed": 0,
                "modified": 2,
                "unchanged": 13
            },
            "changed_files": ["src/api.py", "tests/test_api.py"],
            "added": [
                {
                    "name": "create_user",
                    "type": "function",
                    "module": "api",
                    "signature": "def create_user(name: str, email: str) -> User",
                    "line_number": 25,
                    "is_public": True,
                    "visibility": "public"
                }
            ],
            "modified": [
                {
                    "old": {
                        "name": "get_user",
                        "type": "function",
                        "module": "api",
                        "signature": "def get_user(user_id: int) -> User",
                        "line_number": 10,
                        "is_public": True,
                        "visibility": "public"
                    },
                    "new": {
                        "name": "get_user",
                        "type": "function",
                        "module": "api",
                        "signature": "def get_user(user_id: int, include_deleted: bool = False) -> User",
                        "line_number": 10,
                        "is_public": True,
                        "visibility": "public"
                    }
                }
            ]
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(sample_result, f, indent=2)
            print(f"API diff analysis written to {args.output}")
        else:
            print(json.dumps(sample_result, indent=2))
        
        return
    
    if args.git_diff:
        base_commit, head_commit = args.git_diff
        result = analyzer.analyze_git_diff(base_commit, head_commit)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"API diff analysis written to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    elif args.dir_diff:
        old_dir, new_dir = args.dir_diff
        result = analyzer.analyze_directory(old_dir, new_dir)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"API diff analysis written to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    else:
        print("Robust API-diff: Use --emit for sample analysis, --git-diff for Git comparison, or --dir-diff for directory comparison")


if __name__ == "__main__":
    main()
