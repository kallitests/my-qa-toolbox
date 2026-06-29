// Démonstration cy.aiAssert() sur une mini-app locale (cypress/fixtures/demo-app.html)
// — évite toute dépendance à un site externe pour faire tourner la démo/CI.

describe('cy.aiAssert — validation sémantique', () => {
  beforeEach(() => {
    cy.visit('cypress/fixtures/demo-app.html');
  });

  it('le panier est vide au chargement', () => {
    cy.aiAssert('le panier affiche bien 0 article');
  });

  it('une recherche affiche des résultats', () => {
    cy.get('#search').type('clavier mécanique');
    cy.get('#search-btn').click();
    cy.aiAssert('la page affiche un résultat de recherche mentionnant des produits trouvés');
  });
});
