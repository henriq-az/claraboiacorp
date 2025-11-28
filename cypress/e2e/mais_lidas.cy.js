// cypress/e2e/mais_lidas.cy.js
describe('Mais Lidas navigation', () => {
  beforeEach(() => {
    // Visita a página inicial antes de cada teste
    cy.visit('/');
  });

  it('navigates to /mais-lidas/ when clicking the Mais Lidas menu link', () => {
    // Abrir o menu hamburguer
    cy.get('#menuHamburguer', { timeout: 10000 }).should('be.visible').click();

    // Aguardar o menu lateral e clicar no link 'Mais Lidas'
    cy.get('.menu-lateral', { timeout: 5000 }).should('be.visible');
    cy.get('.menu-lateral').contains('a.menu-link', 'Mais Lidas').should('be.visible').click();

    // Verifica que a URL mudou para /mais-lidas (aceita com ou sem trailing slash)
    cy.location('pathname').should((path) => {
      expect(path.replace(/\/+$/,'')).to.match(/\/mais-lidas$/);
    });

    // Verifica que a rota responde com 200
    cy.request('/mais-lidas/').its('status').should('eq', 200);
  });
});
