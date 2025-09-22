#!/usr/bin/env python3
"""
Pack Evidence Script for Proof Engine for Code
Generates a zip file containing all proof artifacts for verification
"""
import os
import zipfile
import sys
import json
from pathlib import Path

def pack_evidence(output_file="grove-v0.1.1.zip"):
    """Pack all proof artifacts into a zip file"""
    
    # List of proof artifacts to include
    files = [
        ".proof/journal.ndjson",
        ".proof/merkle.json", 
        ".proof/ruff.json",
        ".proof/sast.json",
        ".proof/sbom.json",
        ".proof/coverage.xml",
        ".proof/test-report.xml",
        ".proof/api_diff.json",
        ".proof/build_manifest.json",
        "README_VERIFY.md"
    ]
    
    print(f"📦 Packing evidence artifacts into {output_file}...")
    
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as z:
        included_count = 0
        
        for file_path in files:
            if os.path.exists(file_path):
                z.write(file_path)
                included_count += 1
                print(f"  ✅ {file_path}")
            else:
                print(f"  ⚠️  {file_path} (missing)")
        
        # Add verification instructions
        verification_instructions = """# Proof Evidence Verification

## Merkle Root Verification

To verify the cryptographic integrity of these proof artifacts:

1. **Extract this zip file**
2. **Recalculate the Merkle root**:
   ```bash
   python spec_pack/tools/merkle_hasher.py --in .proof --out .proof/merkle_verify.json
   ```
3. **Compare with original**:
   ```bash
   diff .proof/merkle.json .proof/merkle_verify.json
   ```
4. **Expected result**: Files should be identical (same Merkle root)

## Artifact Verification

- **merkle.json**: Cryptographic integrity hash
- **ruff.json**: Linting results and code quality
- **sast.json**: Security analysis findings
- **sbom.json**: Software Bill of Materials
- **coverage.xml**: Test coverage metrics
- **test-report.xml**: Test execution results
- **api_diff.json**: API change analysis
- **build_manifest.json**: Build reproducibility data

## Verification Success

If all artifacts verify correctly, the proof evidence demonstrates:
- ✅ **Cryptographic Integrity**: No tampering detected
- ✅ **Code Quality**: Linting and type checking passed
- ✅ **Security**: No critical vulnerabilities found
- ✅ **Testing**: Adequate test coverage achieved
- ✅ **Reproducibility**: Build artifacts are deterministic

This evidence pack proves the code changes meet all quality and security obligations.
"""
        
        z.writestr("VERIFICATION_INSTRUCTIONS.md", verification_instructions)
        included_count += 1
        print(f"  ✅ VERIFICATION_INSTRUCTIONS.md")
    
    print(f"\n🎉 Evidence pack created: {output_file}")
    print(f"📊 Included {included_count} files")
    print(f"📏 Size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    return output_file

def main():
    """Main function"""
    output_file = sys.argv[1] if len(sys.argv) > 1 else "grove-v0.1.1.zip"
    
    print("🔒 Proof Engine for Code - Evidence Packer")
    print("=" * 50)
    
    if not os.path.exists(".proof"):
        print("❌ .proof directory not found")
        print("   Run 'python spec_pack/tools/run_s1.py' first to generate artifacts")
        sys.exit(1)
    
    try:
        pack_evidence(output_file)
        print("\n✅ Evidence pack ready for OpenAI Grove demonstration!")
    except Exception as e:
        print(f"\n❌ Error creating evidence pack: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



