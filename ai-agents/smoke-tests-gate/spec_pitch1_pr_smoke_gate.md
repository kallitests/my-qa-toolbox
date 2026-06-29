# SPEC — Pitch 1 : "PR Smoke Gate" — Suite de smoke tests UI + API < 5 min

---

## 1. Objectif du projet

Démontrer la maîtrise de Playwright TypeScript en construisant une **suite de smoke tests rapide et fiable**, conçue pour s'exécuter en moins de 5 minutes lors d'une pull request ou d'une release — exactement le besoin qu'une équipe de dev attend d'un SDET senior, avant d'investir dans une suite de régression complète.

**Message clé pour un recruteur/client** : "Je sais identifier ce qui mérite d'être testé à chaque PR (vitesse, fiabilité, couverture du critique) — pas juste écrire des tests."

---

## 2. Périmètre — 3 cibles, 3 niveaux de réalisme

Le projet est volontairement structuré en 3 sous-parties, chacune apportant une preuve différente :

| Cible | Ce qu'elle prouve | Type |
|---|---|---|
| **A. Amazon.fr (lecture seule)** | Capacité à tester un vrai site complexe en conditions réelles, sans contrôle du code | UI uniquement |
| **B. Sauce Demo** | Maîtrise des bonnes pratiques sur une app de test dédiée (référence du métier QA) | UI + petite API mockée |
| **C. Next.js Commerce (démo open-source)** | Capacité à combiner UI + API sur une vraie stack moderne, avec contrôle total | UI + API |

Cette structure montre une **progression maîtrisée** : du site externe non contrôlé (le plus dur), à l'app dédiée au testing (le plus propre), jusqu'à une vraie stack e-commerce avec API réelle (le plus complet).

---

## 3. Partie A — Amazon.fr (lecture seule, sans login)

**Reprend et formalise le travail déjà ébauché précédemment.**

### Scope des smoke tests (UI uniquement, ~8-10 tests)
- Chargement de la page d'accueil (titre, status 200)
- Visibilité des éléments critiques du header (logo, recherche, panier, compte)
- Recherche produit → résultats affichés
- Recherche vide → pas de crash
- Accès à la page panier
- Présence du footer
- Responsive basique (viewport mobile)
- Gestion de la bannière cookies (pattern robustesse)

### Contraintes spécifiques
- Pas de login, pas d'achat, pas de données personnelles → reste dans un usage raisonnable et éthique du site
- Sélecteurs à valider/mettre à jour via `codegen` au moment de l'implémentation (peuvent avoir changé)
- Limiter la fréquence d'exécution (pas de run en boucle en CI contre le vrai site — à documenter explicitement dans le README comme bonne pratique)

### Ce que ça démontre
Capacité à tester un site réel à fort trafic, avec des sélecteurs non maîtrisés et des éléments imprévisibles (popups, A/B testing, CAPTCHA potentiel) — la situation la plus proche d'un audit chez un client externe.

---

## 4. Partie B — Sauce Demo (saucedemo.com)

**Pourquoi cette cible** : c'est LA référence du milieu QA pour les démonstrations — un recruteur technique la reconnaîtra immédiatement, et ça montre que vous connaissez les standards du métier.

### Scope des smoke tests (UI, ~10-12 tests)
- Login avec les comptes de test fournis (standard_user, locked_out_user, problem_user)
- Liste des produits affichée correctement
- Ajout d'un produit au panier → badge panier mis à jour
- Tri des produits (prix croissant/décroissant, nom A-Z/Z-A)
- Suppression d'un produit du panier
- Parcours checkout complet (étape infos → vérification → confirmation)
- Logout

### Valeur ajoutée technique à montrer ici
- **Page Object Model complet** (LoginPage, InventoryPage, CartPage, CheckoutPage) — Sauce Demo est l'app idéale pour démontrer une architecture propre car stable et bien structurée
- Tests paramétrés sur les différents comptes de test (`problem_user` génère volontairement des bugs UI — bon test négatif)
- Fixtures de login réutilisables (`storageState` pour éviter de se reconnecter à chaque test)

### Ce que ça démontre
Maîtrise des fondamentaux propres (architecture, fixtures, POM) dans un contexte stable et entièrement contrôlable — la "vitrine technique" du projet.

---

## 5. Partie C — Next.js Commerce (démo open-source)

**Pourquoi cette cible** : c'est le seul terrain qui permet de combiner UI + API réelle sur une stack e-commerce moderne réaliste, avec accès au code si besoin de comprendre la structure.

> Note : vérifier au moment de l'implémentation quel template open-source de démo e-commerce est actif et déployé publiquement (l'écosystème Next.js Commerce évolue) — à défaut, une alternative équivalente (ex: Medusa.js demo store, ou un déploiement Vercel d'un starter e-commerce) fait aussi l'affaire. Le choix précis de la stack est secondaire ; ce qui compte est la combinaison UI + API réelle et déployée.

### Scope des smoke tests (UI + API, ~12-15 tests)
**UI :**
- Page d'accueil → catalogue produits affiché
- Navigation vers une fiche produit
- Ajout au panier → mise à jour visuelle
- Affichage du panier avec le bon total

**API (si endpoints exposés/documentés) :**
- GET liste produits → status 200, structure JSON correcte
- GET détail produit par ID
- Test de cohérence : produit vu en API == produit affiché en UI (pattern combiné API+UI)

### Valeur ajoutée technique à montrer ici
- **Pattern API + UI combiné** : vérifier qu'une donnée récupérée via API correspond à ce qui s'affiche réellement dans l'interface
- Mock de réponse API via `page.route()` pour tester un cas d'erreur (ex: simuler un 500 sur l'API produits → vérifier l'affichage d'un message d'erreur côté UI)
- Mesure et affichage du temps d'exécution total de la suite (objectif < 5 min)

### Ce que ça démontre
La compétence la plus recherchée actuellement : savoir combiner UI et API dans une stratégie de test cohérente, pas les traiter comme deux mondes séparés.

---

## 6. Architecture technique commune aux 3 parties

```
playwright-smoke-portfolio/
├── tests/
│   ├── amazon/
│   │   └── amazon-smoke.spec.ts
│   ├── saucedemo/
│   │   ├── login.spec.ts
│   │   ├── cart.spec.ts
│   │   └── checkout.spec.ts
│   └── nextjs-commerce/
│       ├── ui.spec.ts
│       └── api.spec.ts
├── pages/                      # Page Object Model (saucedemo principalement)
│   ├── LoginPage.ts
│   ├── InventoryPage.ts
│   └── CartPage.ts
├── fixtures/
│   └── auth.fixture.ts
├── playwright.config.ts        # projets séparés par cible, retries CI, trace on-first-retry
├── .github/workflows/
│   └── pr-smoke-gate.yml       # déclenché sur pull_request, objectif < 5 min
└── README.md                   # pitch, résultats, captures du rapport CI
```

---

## 7. Intégration CI/CD (le cœur du pitch)

- **GitHub Actions**, déclenché sur chaque `pull_request`
- Exécution en **parallèle** des 3 projets (`amazon`, `saucedemo`, `nextjs-commerce`) via les `projects` Playwright
- Badge de statut + temps d'exécution affiché dans le README
- Rapport HTML publié comme artifact de la run GitHub Actions
- **Objectif chiffré et mesuré** : durée totale < 5 minutes, affichée explicitement dans le README ("dernière run : 3min42")

C'est ce chiffre concret, mesuré et affiché, qui transforme le projet en preuve plutôt qu'en simple démonstration.

---

## 8. Livrables finaux

1. Repo GitHub public, README clair avec :
   - Le pitch en 3 lignes ("pourquoi ce projet")
   - Architecture du repo
   - Comment lancer en local
   - Capture du rapport CI + temps d'exécution
2. Pipeline GitHub Actions fonctionnel et visible (historique de runs)
3. Un court post LinkedIn ou article expliquant la démarche ("pourquoi des smoke tests < 5 min plutôt qu'une suite E2E complète") — utile pour le partager directement aux commerciaux/recruteurs

---

## 9. Risques / points d'attention à anticiper

- **Amazon** : sélecteurs fragiles, possible CAPTCHA en CI → prévoir un mode "skip si bloqué" documenté plutôt qu'un échec rouge permanent qui dévalorise le projet
- **Next.js Commerce** : dépendance à un service tiers déployé — vérifier sa disponibilité avant de construire dessus, prévoir un fallback
- **Sauce Demo** : le plus stable des trois, à privilégier comme "noyau dur" si le temps est limité

---

## 10. Estimation de temps de réalisation

| Partie | Temps estimé |
|---|---|
| Setup projet + CI de base | 0,5 jour |
| Sauce Demo (POM + fixtures) | 1 jour |
| Amazon (lecture seule) | 0,5 jour |
| Next.js Commerce (UI + API) | 1 jour |
| README + polish + post LinkedIn | 0,5 jour |
| **Total** | **~3,5 jours** |
