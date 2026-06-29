# Prompt réutilisable — génération de commande Cypress boostée IA

Copie-colle ce prompt (remplace `{{PITCH}}`) dans Claude pour générer une nouvelle commande
suivant strictement l'architecture de cy-commands-box. Conçu court pour limiter la conso de tokens.

---

```
Tu génères une commande Cypress custom boostée IA pour le repo cy-commands-box.

CONTRAINTES D'ARCHITECTURE (obligatoires, ne pas dévier) :
- Logique LLM uniquement côté Node, jamais dans le navigateur : commande Cypress = wrapper
  cy.task('nomTache', payload), tâche enregistrée dans cypress.config.ts.
- Sortie LLM structurée via zod + .withStructuredOutput(), jamais de texte libre parsé à la main.
- Client LLM partagé : importer getChatModel() depuis cypress/support/ai/langchainClient.ts,
  ne jamais instancier un nouveau client.
- LangSmith : ne rien coder, le traçage est automatique via les env vars existantes.
- Limiter le payload envoyé au LLM (troncature HTML/texte) pour maîtriser coût et tokens.

PITCH DE LA COMMANDE :
{{PITCH}}

LIVRABLES À PRODUIRE :
1. cypress/support/ai/<nomCommande>.ts — fonction run<NomCommande>(input) avec schéma zod
   et prompt system/human concis.
2. Extrait à ajouter dans cypress.config.ts (entrée du task).
3. Extrait à ajouter dans cypress/support/commands.ts — la commande Cypress.Commands.add(),
   avec déclaration TypeScript globale, + commentaire "valeur métier" en 1 phrase.
4. Un spec de démonstration minimal dans cypress/e2e/ utilisant la fixture
   cypress/fixtures/demo-app.html (ou nouvelle fixture si nécessaire).
5. Un cas d'ajout dans eval/dataset.json (input + résultat attendu) si la commande
   retourne un booléen ou une classification — sinon, le préciser explicitement.

Réponds uniquement avec le code, pas d'explication superflue.
```

---

**Exemple de pitch à coller dans `{{PITCH}}` :**
> "Une commande `cy.aiA11yReview()` qui analyse le DOM de la page courante et identifie
> les 3 problèmes d'accessibilité les plus critiques (contraste, labels manquants, focus),
> avec une suggestion de correction pour chacun."
