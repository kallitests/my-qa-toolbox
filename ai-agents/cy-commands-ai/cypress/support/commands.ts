/// <reference types="cypress" />

// ============================================================
// cy.aiAssert(intent) — Agent de validation sémantique de page
// ============================================================
// Valeur métier : remplace des assertions fragiles ("le texte exact
// est 'Bienvenue'") par une vérification d'intention ("l'utilisateur
// vient bien d'être redirigé vers son tableau de bord après connexion"),
// résiliente aux changements de copywriting/UI mineurs.
Cypress.Commands.add('aiAssert', (intent: string) => {
  cy.document().then((doc) => {
    const html = doc.documentElement.outerHTML.slice(0, 12000); // borne le coût/tokens
    return cy.task('aiAssert', { html, intent, url: doc.location.href }, { log: false }).then((result: any) => {
      cy.log(`🤖 aiAssert: ${result.pass ? '✅' : '❌'} — ${result.reason}`);
      expect(result.pass, `aiAssert("${intent}") → ${result.reason}`).to.be.true;
    });
  });
});

// ============================================================
// cy.aiTriage() — Agent de diagnostic post-échec (sur fail uniquement)
// ============================================================
// Valeur métier : à chaque échec de test, classe automatiquement la
// cause probable (vrai bug / flaky / problème d'environnement) pour
// prioriser le triage humain — gain de temps direct pour l'équipe QA.
Cypress.Commands.add('aiTriage', (errorMessage: string) => {
  cy.document().then((doc) => {
    const html = doc.documentElement.outerHTML.slice(0, 8000);
    return cy.task(
      'aiTriage',
      { testTitle: Cypress.currentTest.title, errorMessage, html },
      { log: false }
    ).then((result: any) => {
      cy.log(`🩺 aiTriage: [${result.category}] (confiance ${result.confidence}) — ${result.reasoning}`);
    });
  });
});

// ====================================================================
// cy.aiGenerateTestCase(userStory) — Agent générateur de cas de test
// ====================================================================
// Valeur métier : accélère la phase de conception de tests à partir
// d'une user story texte libre (PO/QA manuel) — sortie structurée
// directement exploitable (Gherkin-like), pas un texte libre à reformater.
Cypress.Commands.add('aiGenerateTestCase', (userStory: string) => {
  return cy.task('aiGenerateTestCase', { userStory }, { log: false }).then((result: any) => {
    cy.log(`📋 ${result.testCases.length} cas de test générés depuis la user story`);
    return cy.wrap(result.testCases, { log: false });
  });
});

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      aiAssert(intent: string): Chainable<void>;
      aiTriage(errorMessage: string): Chainable<void>;
      aiGenerateTestCase(userStory: string): Chainable<any[]>;
    }
  }
}

export {};
