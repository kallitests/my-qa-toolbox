// Démonstration cy.aiTriage() — appelée volontairement après un échec simulé,
// dans un hook afterEach conditionnel (pattern recommandé en usage réel).

describe('cy.aiTriage — diagnostic post-échec', () => {
  afterEach(function () {
    if (this.currentTest?.state === 'failed') {
      cy.aiTriage(this.currentTest.err?.message || 'unknown error');
    }
  });

  it('échec volontaire pour démontrer le triage IA', () => {
    cy.visit('cypress/fixtures/demo-app.html');
    cy.get('#logo').should('have.text', 'CeTexteNExistePas'); // échec volontaire
  });
});
