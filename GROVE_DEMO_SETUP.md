# Configuration OpenAI Grove Demo

## 🎯 Objectif
Préparer le repository `architect-of-proof` pour la candidature à l'incubateur OpenAI Grove.

## ✅ État actuel
- **Tag de gel** : `v0.1.1-grove` créé et poussé
- **Branche demo** : `demo/grove` créée et poussée
- **Code gelé** : Tous les outils Track A stabilisés (9/10 readiness)

## 🛡️ Configuration de la protection de branche demo/grove

### 1. Accéder aux paramètres du repository
1. Aller sur https://github.com/RomainPeter/architect-of-proof
2. Cliquer sur **Settings** (onglet en haut)
3. Dans le menu de gauche, cliquer sur **Branches**

### 2. Configurer la protection de la branche demo/grove
1. Cliquer sur **Add rule** ou **Add branch protection rule**
2. Dans **Branch name pattern**, entrer : `demo/grove`
3. Configurer les options suivantes :

#### ✅ Required status checks
- [x] **Require status checks to pass before merging**
- [x] **Require branches to be up to date before merging**
- Dans la liste des checks, sélectionner :
  - [x] **code_proof** (obligatoire)

#### ✅ Required pull request reviews
- [x] **Require a pull request before merging**
- [x] **Require approvals** : `1`
- [x] **Dismiss stale PR approvals when new commits are pushed**

#### ✅ Additional protections
- [x] **Require linear history**
- [x] **Require deployments to succeed before merging**

#### ✅ Rules applied to administrators
- [x] **Include administrators**

### 3. Sauvegarder
1. Cliquer sur **Create** ou **Save changes**
2. Confirmer la configuration

## 🚀 Génération d'artefacts frais

Après configuration de la protection, exécuter :

```bash
# Sur la branche demo/grove
git checkout demo/grove

# Commit pour générer des artefacts frais
git commit --allow-empty -m "chore: demo freeze

Generate fresh artifacts for OpenAI Grove demonstration.
This commit triggers all CI/CD workflows to produce clean
artifacts showcasing the full architect-of-proof capabilities.

Artifacts generated:
- .proof/merkle.json: Merkle root for proof integrity
- .proof/coverage.xml: Test coverage report
- .proof/sast.json: Static analysis security report
- .proof/sbom.json: Software Bill of Materials
- spec_pack/samples/journal.ndjson: Proof journal
- spec_pack/samples/incidents.ndjson: Incident tracking

Ready for OpenAI Grove presentation."

# Pousser le commit
git push origin demo/grove
```

## 📋 Artefacts de démonstration

Les artefacts suivants seront générés automatiquement :

### 🔒 Preuves de sécurité
- **Merkle Root** : Intégrité cryptographique des preuves
- **SAST Report** : Analyse statique de sécurité
- **SBOM** : Inventaire des dépendances avec vulnérabilités

### 📊 Métriques de qualité
- **Coverage Report** : Couverture de tests détaillée
- **Linting Report** : Conformité aux standards de code
- **Type Checking** : Vérification de types statique

### 📝 Journalisation
- **Proof Journal** : Traçabilité complète des preuves
- **Incident Log** : Gestion des incidents de sécurité

## 🎯 Points de démonstration pour OpenAI Grove

### 1. **Architecture de preuve formelle**
- Système de preuves cryptographiques avec Merkle trees
- Traçabilité complète des obligations de code
- Intégrité des artefacts de build

### 2. **Sécurité automatisée**
- SAST (Static Application Security Testing)
- OSV (Open Source Vulnerabilities) integration
- Gating de sécurité basé sur les chemins

### 3. **Qualité de code**
- Vérification de types avec dmypy
- Linting avec ruff
- Tests automatisés avec pytest

### 4. **Reproductibilité**
- Pinning des dépendances avec UV
- Docker digest pinning
- Lock files cryptographiquement vérifiés

### 5. **Analyse de différences API**
- Détection robuste des changements d'API
- Classification BREAKING/MINOR/PATCH
- Cache AST pour performance

## 🔍 Vérification finale

1. **Vérifier la protection** : Créer une PR vers `demo/grove`
2. **Confirmer les checks** : `code_proof` doit être requis
3. **Valider les artefacts** : Tous les fichiers `.proof/` doivent être présents
4. **Tester la démo** : Workflows Proof Delta, Proof CI, Proof Nightly

## 📞 Prêt pour l'entretien OpenAI Grove

Le repository est maintenant configuré pour une démonstration complète des capacités d'architecture de preuve formelle, avec tous les artefacts de sécurité et de qualité nécessaires pour impressionner l'équipe OpenAI Grove.


## Demo Ambition Intake v0 (CLI uniquement)

```bash
# 1) Installer en editable
python -m pip install -e .

# 2) Générer un ambition.json (assistant interactif)
pec ambition init

# 3) Valider
pec ambition validate

# 4) Compiler (génère .pec/obligations.lock + .pec/proof_delta.md)
pec ambition compile

# 5) Afficher le Proof Delta
cat .pec/proof_delta.md
```

Notes:
- Fichier schéma: `.pec/ambition.schema.json`
- Fichier ambition: `.pec/ambition.json`
- Sorties: `.pec/obligations.lock`, `.pec/proof_delta.md`
