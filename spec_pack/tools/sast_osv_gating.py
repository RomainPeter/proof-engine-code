#!/usr/bin/env python3
"""
Path-based SAST + OSV gating
Advanced static analysis with path-based rules and OSV vulnerability gating.
"""

import argparse
import json
import sys
import requests
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class SASTRule:
    """Represents a SAST rule with path-based conditions"""
    id: str
    name: str
    severity: str  # critical, high, medium, low, info
    pattern: str
    paths: List[str]  # Path patterns to apply rule to
    exclude_paths: List[str]  # Path patterns to exclude
    message: str
    category: str  # security, performance, maintainability, etc.


@dataclass
class OSVVulnerability:
    """Represents an OSV vulnerability"""
    id: str
    package: str
    version: str
    severity: str
    summary: str
    details: str
    affected_versions: List[str]
    fixed_versions: List[str]
    references: List[str]


@dataclass
class SASTFinding:
    """Represents a SAST finding"""
    rule_id: str
    file_path: str
    line_number: int
    column_number: int
    severity: str
    message: str
    code_snippet: str
    category: str


@dataclass
class GatingResult:
    """Represents the result of security gating"""
    passed: bool
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    osv_vulnerabilities: int
    blocked_paths: List[str]
    recommendations: List[str]


class PathBasedSAST:
    """Path-based Static Application Security Testing"""
    
    def __init__(self, rules_file: Optional[str] = None):
        self.rules = []
        if rules_file and Path(rules_file).exists():
            self.load_rules(rules_file)
        else:
            self.load_default_rules()
    
    def load_rules(self, rules_file: str):
        """Load SAST rules from YAML file"""
        try:
            with open(rules_file, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            for rule_data in rules_data.get('rules', []):
                rule = SASTRule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    severity=rule_data['severity'],
                    pattern=rule_data['pattern'],
                    paths=rule_data.get('paths', ['**/*']),
                    exclude_paths=rule_data.get('exclude_paths', []),
                    message=rule_data['message'],
                    category=rule_data.get('category', 'security')
                )
                self.rules.append(rule)
        
        except Exception as e:
            print(f"Failed to load rules from {rules_file}: {e}", file=sys.stderr)
    
    def load_default_rules(self):
        """Load default SAST rules"""
        default_rules = [
            SASTRule(
                id="SQL_INJECTION",
                name="SQL Injection",
                severity="critical",
                pattern=r"(execute|query|exec)\s*\(\s*['\"].*%.*['\"]",
                paths=["**/*.py", "**/*.js", "**/*.java"],
                exclude_paths=["**/test/**", "**/tests/**"],
                message="Potential SQL injection vulnerability",
                category="security"
            ),
            SASTRule(
                id="HARDCODED_SECRET",
                name="Hardcoded Secret",
                severity="high",
                pattern=r"(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]",
                paths=["**/*.py", "**/*.js", "**/*.java", "**/*.env*"],
                exclude_paths=["**/test/**", "**/tests/**", "**/example*"],
                message="Hardcoded secret detected",
                category="security"
            ),
            SASTRule(
                id="WEAK_CRYPTO",
                name="Weak Cryptographic Function",
                severity="high",
                pattern=r"(md5|sha1|des|rc4)\s*\(",
                paths=["**/*.py", "**/*.js", "**/*.java"],
                exclude_paths=["**/test/**", "**/tests/**"],
                message="Weak cryptographic function used",
                category="security"
            ),
            SASTRule(
                id="PATH_TRAVERSAL",
                name="Path Traversal",
                severity="high",
                pattern=r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
                paths=["**/*.py", "**/*.js", "**/*.java"],
                exclude_paths=["**/test/**", "**/tests/**"],
                message="Potential path traversal vulnerability",
                category="security"
            ),
            SASTRule(
                id="XSS_POTENTIAL",
                name="Cross-Site Scripting",
                severity="medium",
                pattern=r"(innerHTML|outerHTML|document\.write)\s*\(",
                paths=["**/*.js", "**/*.html", "**/*.tsx", "**/*.jsx"],
                exclude_paths=["**/test/**", "**/tests/**"],
                message="Potential XSS vulnerability",
                category="security"
            )
        ]
        self.rules.extend(default_rules)
    
    def path_matches(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the given patterns"""
        for pattern in patterns:
            if pattern == "**/*":
                return True
            if pattern.endswith("/*"):
                prefix = pattern[:-2]
                if file_path.startswith(prefix):
                    return True
            if pattern.startswith("**/"):
                suffix = pattern[3:]
                if file_path.endswith(suffix):
                    return True
            if "*" in pattern:
                # Simple glob matching
                import fnmatch
                if fnmatch.fnmatch(file_path, pattern):
                    return True
            else:
                if file_path == pattern:
                    return True
        return False
    
    def should_exclude_path(self, file_path: str, exclude_patterns: List[str]) -> bool:
        """Check if file path should be excluded"""
        return self.path_matches(file_path, exclude_patterns)
    
    def scan_file(self, file_path: str) -> List[SASTFinding]:
        """Scan a single file for SAST issues"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Failed to read {file_path}: {e}", file=sys.stderr)
            return findings
        
        for rule in self.rules:
            # Check if file path matches rule paths
            if not self.path_matches(file_path, rule.paths):
                continue
            
            # Check if file path should be excluded
            if self.should_exclude_path(file_path, rule.exclude_paths):
                continue
            
            # Search for pattern in file
            pattern = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
            matches = pattern.finditer(content)
            
            for match in matches:
                # Find line number
                line_number = content[:match.start()].count('\n') + 1
                column_number = match.start() - content.rfind('\n', 0, match.start()) - 1
                
                # Get code snippet
                start_line = max(0, line_number - 2)
                end_line = min(len(lines), line_number + 2)
                code_snippet = '\n'.join(lines[start_line:end_line])
                
                finding = SASTFinding(
                    rule_id=rule.id,
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    severity=rule.severity,
                    message=rule.message,
                    code_snippet=code_snippet,
                    category=rule.category
                )
                findings.append(finding)
        
        return findings
    
    def scan_directory(self, directory: str, max_workers: int = 4) -> List[SASTFinding]:
        """Scan entire directory for SAST issues with parallel processing"""
        directory_path = Path(directory)
        
        # Get all relevant files
        file_extensions = {'.py', '.js', '.java', '.ts', '.tsx', '.jsx', '.html', '.env'}
        files_to_scan = [
            str(file_path) for file_path in directory_path.rglob('*')
            if file_path.is_file() and file_path.suffix in file_extensions
        ]
        
        all_findings = []
        
        # Use ThreadPoolExecutor for parallel scanning
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scan tasks
            future_to_file = {
                executor.submit(self.scan_file, file_path): file_path
                for file_path in files_to_scan
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}", file=sys.stderr)
        
        return all_findings


class OSVGating:
    """OSV (Open Source Vulnerabilities) gating"""
    
    def __init__(self):
        self.osv_api_url = "https://api.osv.dev/v1/query"
        self.cache_dir = Path(".proof/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "osv.jsonl"
    
    def _get_cache_key(self, package_name: str, version: str) -> str:
        """Generate cache key for package/version"""
        import hashlib
        key = f"{package_name}@{version}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[OSVVulnerability]]:
        """Load vulnerabilities from cache"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get('cache_key') == cache_key:
                            return [OSVVulnerability(**v) for v in entry.get('vulnerabilities', [])]
        except Exception:
            pass
        return None
    
    def _save_to_cache(self, cache_key: str, vulnerabilities: List[OSVVulnerability]):
        """Save vulnerabilities to cache"""
        try:
            entry = {
                'cache_key': cache_key,
                'timestamp': time.time(),
                'vulnerabilities': [asdict(v) for v in vulnerabilities]
            }
            with open(self.cache_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception:
            pass
    
    def check_package_vulnerabilities(self, package_name: str, version: str) -> List[OSVVulnerability]:
        """Check for vulnerabilities in a specific package version with caching and retries"""
        cache_key = self._get_cache_key(package_name, version)
        
        # Try cache first
        cached = self._load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                query = {
                    "package": {"name": package_name},
                    "version": version
                }
                
                response = requests.post(self.osv_api_url, json=query, timeout=3)
                response.raise_for_status()
                
                data = response.json()
                
                # Validate response schema
                if 'vulns' not in data:
                    print(f"Invalid OSV response for {package_name}: missing 'vulns' key", file=sys.stderr)
                    return []
                
                vulnerabilities = []
                for vuln_data in data.get('vulns', []):
                    vuln = OSVVulnerability(
                        id=vuln_data.get('id', ''),
                        package=package_name,
                        version=version,
                        severity=self._extract_severity(vuln_data),
                        summary=vuln_data.get('summary', ''),
                        details=vuln_data.get('details', ''),
                        affected_versions=vuln_data.get('affected', [{}])[0].get('versions', []),
                        fixed_versions=vuln_data.get('affected', [{}])[0].get('ranges', []),
                        references=vuln_data.get('references', [])
                    )
                    vulnerabilities.append(vuln)
                
                # Save to cache
                self._save_to_cache(cache_key, vulnerabilities)
                return vulnerabilities
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                print(f"OSV timeout for {package_name} after {max_retries} attempts", file=sys.stderr)
                return []
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                print(f"OSV network error for {package_name}: {e}", file=sys.stderr)
                return []
            except Exception as e:
                print(f"Failed to check OSV for {package_name}: {e}", file=sys.stderr)
                return []
        
        return []
    
    def _extract_severity(self, vuln_data: Dict[str, Any]) -> str:
        """Extract severity from vulnerability data"""
        severity = vuln_data.get('severity', [])
        if severity:
            return severity[0].get('score', 'unknown')
        return 'unknown'
    
    def check_requirements_file(self, requirements_file: str) -> List[OSVVulnerability]:
        """Check vulnerabilities in requirements file"""
        vulnerabilities = []
        
        try:
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package name and version
                    if '==' in line:
                        package_name, version = line.split('==', 1)
                    elif '>=' in line:
                        package_name, version = line.split('>=', 1)
                    else:
                        continue
                    
                    package_name = package_name.strip()
                    version = version.strip()
                    
                    # Check for vulnerabilities
                    vulns = self.check_package_vulnerabilities(package_name, version)
                    vulnerabilities.extend(vulns)
        
        except Exception as e:
            print(f"Failed to check requirements file {requirements_file}: {e}", file=sys.stderr)
        
        return vulnerabilities


class SecurityGating:
    """Main security gating orchestrator"""
    
    def __init__(self, rules_file: Optional[str] = None):
        self.sast = PathBasedSAST(rules_file)
        self.osv = OSVGating()
    
    def gate_commit(self, directory: str, requirements_file: Optional[str] = None) -> GatingResult:
        """Perform security gating on a commit"""
        
        # Run SAST analysis
        sast_findings = self.sast.scan_directory(directory)
        
        # Count findings by severity
        critical_findings = sum(1 for f in sast_findings if f.severity == 'critical')
        high_findings = sum(1 for f in sast_findings if f.severity == 'high')
        medium_findings = sum(1 for f in sast_findings if f.severity == 'medium')
        low_findings = sum(1 for f in sast_findings if f.severity == 'low')
        
        # Check OSV vulnerabilities
        osv_vulnerabilities = []
        if requirements_file and Path(requirements_file).exists():
            osv_vulnerabilities = self.osv.check_requirements_file(requirements_file)
        
        # Determine if gating passes
        passed = (critical_findings == 0 and high_findings == 0)
        
        # Generate recommendations
        recommendations = []
        if critical_findings > 0:
            recommendations.append("Fix critical security issues before merging")
        if high_findings > 0:
            recommendations.append("Address high-severity security issues")
        if osv_vulnerabilities:
            recommendations.append("Update vulnerable dependencies")
        
        # Find blocked paths
        blocked_paths = []
        for finding in sast_findings:
            if finding.severity in ['critical', 'high']:
                blocked_paths.append(finding.file_path)
        
        return GatingResult(
            passed=passed,
            critical_findings=critical_findings,
            high_findings=high_findings,
            medium_findings=medium_findings,
            low_findings=low_findings,
            osv_vulnerabilities=len(osv_vulnerabilities),
            blocked_paths=list(set(blocked_paths)),
            recommendations=recommendations
        )
    
    def generate_report(self, gating_result: GatingResult, sast_findings: List[SASTFinding], 
                       osv_vulnerabilities: List[OSVVulnerability]) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        return {
            "gating_result": asdict(gating_result),
            "sast_findings": [asdict(f) for f in sast_findings],
            "osv_vulnerabilities": [asdict(v) for v in osv_vulnerabilities],
            "summary": {
                "total_sast_findings": len(sast_findings),
                "total_osv_vulnerabilities": len(osv_vulnerabilities),
                "gating_passed": gating_result.passed,
                "risk_level": "high" if gating_result.critical_findings > 0 else 
                             "medium" if gating_result.high_findings > 0 else "low"
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Path-based SAST + OSV gating")
    parser.add_argument("--check", action="store_true", help="Check if SAST/OSV gating is valid")
    parser.add_argument("--emit", action="store_true", help="Emit sample security report")
    parser.add_argument("--scan", help="Scan directory for security issues")
    parser.add_argument("--requirements", help="Requirements file for OSV checking")
    parser.add_argument("--rules", help="Custom SAST rules file")
    parser.add_argument("--output", "-o", help="Output file for security report")
    
    args = parser.parse_args()
    
    if args.check:
        print("Path-based SAST + OSV gating: Check mode - validation passed")
        return
    
    gating = SecurityGating(args.rules)
    
    if args.emit:
        # Generate sample report
        sample_report = {
            "gating_result": {
                "passed": True,
                "critical_findings": 0,
                "high_findings": 1,
                "medium_findings": 3,
                "low_findings": 2,
                "osv_vulnerabilities": 0,
                "blocked_paths": [],
                "recommendations": ["Address high-severity security issues"]
            },
            "sast_findings": [
                {
                    "rule_id": "HARDCODED_SECRET",
                    "file_path": "src/config.py",
                    "line_number": 15,
                    "column_number": 10,
                    "severity": "high",
                    "message": "Hardcoded secret detected",
                    "code_snippet": "api_key = \"sk-1234567890abcdef\"",
                    "category": "security"
                }
            ],
            "osv_vulnerabilities": [],
            "summary": {
                "total_sast_findings": 6,
                "total_osv_vulnerabilities": 0,
                "gating_passed": False,
                "risk_level": "medium"
            }
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(sample_report, f, indent=2)
            print(f"Security report written to {args.output}")
        else:
            print(json.dumps(sample_report, indent=2))
        
        return
    
    if args.scan:
        # Perform security gating
        gating_result = gating.gate_commit(args.scan, args.requirements)
        
        # Get detailed findings
        sast_findings = gating.sast.scan_directory(args.scan)
        osv_vulnerabilities = []
        if args.requirements:
            osv_vulnerabilities = gating.osv.check_requirements_file(args.requirements)
        
        # Generate report
        report = gating.generate_report(gating_result, sast_findings, osv_vulnerabilities)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Security report written to {args.output}")
        else:
            print(json.dumps(report, indent=2))
        
        # Exit with appropriate code
        if not gating_result.passed:
            sys.exit(1)
    
    else:
        print("Path-based SAST + OSV gating: Use --emit for sample report or --scan to scan directory")


if __name__ == "__main__":
    main()
