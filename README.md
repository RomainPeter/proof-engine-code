# Proof Engine for Code — Lite

[![CI](https://github.com/RomainPeter/proof-engine-code/workflows/code_proof/badge.svg)](https://github.com/RomainPeter/proof-engine-code/actions)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **Minimal proof engine for code changes** — Open-core implementation with cryptographic integrity, automated security gating, and comprehensive quality assurance.

## 🎯 What it is

Proof Engine for Code is a **minimal proof engine** that enforces code quality and security through cryptographic integrity checks, automated static analysis, and comprehensive testing. It provides:

- **🔒 Cryptographic Integrity**: Merkle tree-based proof journaling
- **🛡️ Security Gating**: SAST, OSV vulnerability scanning, and path-based rules
- **📊 Quality Assurance**: Linting, type checking, test coverage, and API diff analysis
- **🔄 Reproducibility**: UV lock files, Docker digest pinning, and build manifest generation
- **📝 Proof Delta**: Automated PR analysis with detailed change reports

## 🚀 Quickstart

### For Third-Party Repositories

1. **Create a workflow file** `.github/workflows/proof.yml`:

```yaml
name: CI with Proof Engine for Code (Lite)
on: [push, pull_request]

jobs:
  proof:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: RomainPeter/proof-engine-code@v0.1.1
```

2. **Open a PR** and observe:
   - ✅ **`code_proof`** status check running
   - 📝 **Proof Delta** comment with detailed analysis
   - 🔒 **Proof artifacts** generated in `.proof/`

### For This Repository

```bash
# Clone and setup
git clone https://github.com/RomainPeter/proof-engine-code.git
cd proof-engine-code

# Install dependencies
python -m pip install --require-hashes -r spec_pack/requirements.lock.txt

# Run S1 checks (minimal obligations)
python spec_pack/tools/run_s1.py

# Verify proof artifacts
ls .proof/
# merkle.json, ruff.json, sast.json, sbom.json, coverage.xml, test-report.xml
```

## 📋 Four Scenarios

### 1. **Comment-Only Changes**
- Documentation updates, README changes
- **Proof Delta**: Minimal impact, no security concerns
- **Gating**: Passes with low-risk classification

### 2. **Behavior Changes**
- Bug fixes, performance improvements
- **Proof Delta**: Behavior analysis, test coverage impact
- **Gating**: Requires test updates, coverage validation

### 3. **Interface Gate**
- API changes, function signatures
- **Proof Delta**: Breaking vs. minor vs. patch classification
- **Gating**: Requires API diff analysis, semantic versioning

### 4. **Dependencies**
- Package updates, security patches
- **Proof Delta**: Dependency impact analysis
- **Gating**: OSV vulnerability scanning, SBOM generation

## 🔍 Verify Evidence

All proof artifacts can be independently verified:

```bash
# Recalculate Merkle root
python spec_pack/tools/merkle_hasher.py --in .proof --out .proof/merkle_verify.json

# Compare with original
diff .proof/merkle.json .proof/merkle_verify.json
# Should be identical (same Merkle root)
```

**Merkle Root Verification**: The cryptographic integrity of all proof artifacts is guaranteed through Merkle tree hashing. Any modification to the evidence will result in a different root hash, ensuring tamper detection.

## 📁 Generated Artifacts

| Artifact | Purpose | Format |
|----------|---------|--------|
| `.proof/merkle.json` | Cryptographic integrity | JSON |
| `.proof/ruff.json` | Linting results | JSON |
| `.proof/sast.json` | Security analysis | JSON |
| `.proof/sbom.json` | Software Bill of Materials | JSON |
| `.proof/coverage.xml` | Test coverage | XML |
| `.proof/test-report.xml` | Test results | XML |
| `.proof/api_diff.json` | API change analysis | JSON |
| `.proof/build_manifest.json` | Build reproducibility | JSON |

## 🏗️ Architecture

```
spec_pack.code/           # Core specifications
├── obligations_code.yaml # Code quality obligations
├── invariants_code.yaml  # Invariant definitions
└── app/verifiers.yaml    # Verifier configurations

spec_pack/tools/          # Proof generation tools
├── merkle_hasher.py      # Cryptographic integrity
├── run_s1.py            # S1 minimal obligations
├── build_pinning.py     # Reproducibility
├── robust_api_diff.py   # API change analysis
└── sast_osv_gating.py   # Security gating

examples/pilot-python/    # Example implementation
├── src/                 # Source code
└── tests/               # Test suite
```

## 🔧 Configuration

### Obligations (spec_pack.code/obligations_code.yaml)
```yaml
O-CODE-LINT-1: "Code must pass linting (ruff)"
O-CODE-TEST-1: "Code must have test coverage > 80%"
O-CODE-SAST-1: "Code must pass security analysis"
O-CODE-SBOM-1: "Dependencies must be inventoried"
```

### Verifiers (spec_pack.code/app/verifiers.yaml)
```yaml
linter:
  command: "ruff check {path} --output-format json --output-file .proof/ruff.json --exit-zero"
  
typecheck:
  command: "dmypy run -- {path}"
  
test_coverage:
  command: "pytest {path} --cov={path} --cov-report=xml:.proof/coverage.xml"
```

## 📜 Licensing

**Open Source**: This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

**Commercial License**: For commercial use without AGPL obligations, a commercial license is available. Contact: [your-email@domain.com]

### Dual Licensing Model
- **AGPL-3.0**: Free for open source projects
- **Commercial**: Available for proprietary/commercial use

## ⚠️ Limitations

This is the **open-core** version with the following limitations:

- **FCA Canonical**: Formal Concept Analysis with NextClosure algorithm (NotImplemented guard)
- **Advanced Implication Rules**: Complex logical inference rules (NotImplemented guard)
- **Enterprise Features**: Advanced analytics, custom rule engines, enterprise support

For the full-featured version with all capabilities, contact us for commercial licensing.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all `code_proof` checks pass
5. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/RomainPeter/proof-engine-code/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RomainPeter/proof-engine-code/discussions)
- **Commercial**: [your-email@domain.com]

## 🏆 Acknowledgments

Built for the **OpenAI Grove** incubator program, demonstrating advanced code quality assurance and cryptographic proof systems for modern software development.

---

**Ready to prove your code?** 🚀 Start with the [Quickstart](#-quickstart) guide above!