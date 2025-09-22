# Configuration de la Protection de Branche

## 🛡️ Configuration requise pour main

### 1. Accéder aux paramètres du repository
1. Aller sur https://github.com/RomainPeter/architect-of-proof
2. Cliquer sur **Settings** (onglet en haut)
3. Dans le menu de gauche, cliquer sur **Branches**

### 2. Configurer la protection de la branche main
1. Cliquer sur **Add rule** ou **Add branch protection rule**
2. Dans **Branch name pattern**, entrer : `main`
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
- [ ] **Require review from code owners** (optionnel)

#### ✅ Restrictions
- [x] **Restrict pushes that create files**
- [x] **Restrict pushes that delete files**
- [ ] **Restrict pushes that create files larger than 100 MB**

#### ✅ Additional protections
- [x] **Require linear history**
- [x] **Require deployments to succeed before merging**
- [ ] **Require conversation resolution before merging**

#### ✅ Rules applied to administrators
- [x] **Include administrators**

### 3. Sauvegarder
1. Cliquer sur **Create** ou **Save changes**
2. Confirmer la configuration

## 🎯 Résultat attendu

Après configuration, la branche `main` sera protégée avec :
- ✅ **code_proof** status check obligatoire
- ✅ Reviews de PR requis (1 approbation)
- ✅ Historique linéaire obligatoire
- ✅ Administrateurs inclus dans les restrictions
- ✅ Force push et suppression de branche interdits

## 🔍 Vérification

Pour vérifier que la protection fonctionne :
1. Créer une PR vers `main`
2. Vérifier que le check **code_proof** apparaît
3. Confirmer que la PR ne peut pas être mergée sans que **code_proof** passe

## 📋 Status Checks disponibles

Les status checks suivants sont configurés dans le repository :
- **code_proof** : Vérification complète (tests, linting, sécurité, SBOM, etc.)
- **proof-ci** : CI rapide (S1)
- **proof-delta** : Analyse de PR avec rapport détaillé

## ⚠️ Notes importantes

- La protection de branche ne peut être configurée que par un administrateur du repository
- Une fois activée, tous les merges vers `main` devront passer par des PRs avec les checks requis
- Les commits directs sur `main` seront bloqués (sauf pour les administrateurs si l'option est désactivée)

