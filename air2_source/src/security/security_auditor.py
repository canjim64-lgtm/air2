"""
Unified Security Auditor for AirOne Professional v4.0
Performs automated static analysis for hardcoded secrets, unsafe shell commands, and crypto integrity.
"""
import logging
import os
import re
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SecurityAuditor:
    def __init__(self, target_dir: str = "."):
        self.logger = logging.getLogger(f"{__name__}.SecurityAuditor")
        self.target_dir = target_dir
        self.findings = []
        # Fixed regex patterns with proper escaping
        self.vulnerability_patterns = {
            "HARDCODED_SECRET": r"(password|api_key|secret|token)\s*=\s*['\"]([^'\"]+)['\"]",
            "UNSAFE_SHELL": r"os\.system\(|subprocess\.Popen\(.*shell=True|(?<!\.)\beval\(",
            "INSECURE_CRYPTO": r"hashlib\.md5\(|hashlib\.sha1\(|pycrypto",
            "DEBUG_EXPOSURE": r"debug=True|print\(.*password"
        }
        self.logger.info("Unified Security Auditor Initialized.")

    def run_full_audit(self) -> Dict[str, Any]:
        """Scans the entire codebase for common vulnerabilities."""
        self.findings = []
        for root, _, files in os.walk(self.target_dir):
            if "pycache" in root or ".git" in root: continue
            
            for file in files:
                if file.endswith('.py') or file.endswith('.ini') or file.endswith('.json'):
                    self._audit_file(os.path.join(root, file))
        
        severity_counts = {
            "HIGH": sum(1 for f in self.findings if f['severity'] == "HIGH"),
            "MEDIUM": sum(1 for f in self.findings if f['severity'] == "MEDIUM"),
            "LOW": sum(1 for f in self.findings if f['severity'] == "LOW")
        }
        
        return {
            "audit_timestamp": time.time(),
            "total_files_scanned": "Recursive Scan",
            "findings": self.findings,
            "summary": severity_counts,
            "status": "SECURE" if severity_counts['HIGH'] == 0 else "VULNERABLE"
        }

    def _audit_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            content_no_comments = ""
            for line in lines:
                # Basic comment stripping (doesn't handle # inside strings, but better than nothing)
                code_part = line.split('#')[0]
                content_no_comments += code_part + "\n"
                
            for v_type, pattern in self.vulnerability_patterns.items():
                matches = re.finditer(pattern, content_no_comments, re.IGNORECASE)
                for match in matches:
                    if len(match.group(0)) > 500: continue
                    
                    line_no = content_no_comments.count('\n', 0, match.start()) + 1
                    severity = "HIGH" if v_type in ["HARDCODED_SECRET", "UNSAFE_SHELL"] else "MEDIUM"
                    
                    self.findings.append({
                        "file": file_path,
                        "line": line_no,
                        "type": v_type,
                        "severity": severity,
                        "context": match.group(0)[:100]
                    })
        except Exception as e:
            self.logger.error(f"Failed to audit {file_path}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    auditor = SecurityAuditor(target_dir="src")
    report = auditor.run_full_audit()
    print(f"Audit Complete. Summary: {report['summary']}")
