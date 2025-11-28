// cypress/e2e/neels.cy.js
describe('Neels navigation', () => {
  beforeEach(() => {
    // Visita a página inicial antes de cada teste
    cy.visit('/');
  });

  it('navigates to /neels/ when clicking the Neels nav item', () => {
    // Abrir o menu hamburguer e clicar no link 'Neels' dentro do menu lateral
    cy.get('#menuHamburguer', { timeout: 10000 }).should('be.visible').click();

    // Agora procurar o link no menu lateral (classe `menu-link` com texto 'Neels')
    cy.get('.menu-lateral', { timeout: 5000 }).should('be.visible');
    cy.get('.menu-lateral').contains('a.menu-link', 'Neels').should('be.visible').click();

    // Verifica que a URL mudou para /neels/ (trim trailing slash inconsistencies)
    cy.location('pathname').should((path) => {
      // normalizar: aceitar '/neels' ou '/neels/'
      expect(path.replace(/\/+$/,'')).to.match(/\/neels$/);
    });

    // Verifica que a rota responde com 200 (opcional, útil para CI)
    cy.request('/neels/').its('status').should('eq', 200);
  });
});
