// Démonstration cy.aiGenerateTestCase() — génère des cas de test depuis
// une user story, puis les affiche dans le rapport (pas d'assertion ici :
// commande de productivité, pas de validation).

describe('cy.aiGenerateTestCase — génération de cas de test', () => {
  it('génère des cas de test depuis une user story', () => {
    const userStory =
      'En tant qu\'utilisateur connecté, je veux ajouter un produit au panier ' +
      'pour pouvoir le retrouver à l\'étape de paiement.';

    cy.aiGenerateTestCase(userStory).then((testCases) => {
      cy.task('table', testCases, { log: false }); // visible dans cypress run --reporter
      expect(testCases.length).to.be.greaterThan(0);
    });
  });
});
