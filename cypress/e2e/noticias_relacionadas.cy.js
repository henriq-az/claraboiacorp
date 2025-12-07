describe('Teste E2E - Notícias Relacionadas', () => {
  it('Abre uma notícia, rola até "relacionadas" e clica em uma relacionada', () => {
    // Visita a home
    cy.visit('/')

    // Clica no primeiro card de notícia disponível (tenta múltiplos seletores)
    cy.get('.card.top, .card.side, .news-item, a[href*="/"][class*="card"]', { timeout: 10000 })
      .should('exist')
      .and('be.visible')
      .first()
      .click({ force: true })

    // Verifica que abriu uma página de notícia
    cy.url().should('match', /\/[^\s]+\/$/)
    cy.wait(800)

    // Aguarda e rola até a lista de relacionadas
    cy.get('.relacionadas-lista', { timeout: 10000 }).should('exist')
    cy.get('.relacionadas-lista').scrollIntoView({ duration: 800 })
    cy.wait(500)

    // Verifica que existem itens relacionados
    cy.get('.relacionadas-item').should('have.length.at.least', 1)

    // Clica no primeiro item relacionado
    cy.get('.relacionadas-item').first().click({ force: true })

    // Verifica que navegou para a página da notícia clicada
    cy.get('.noticia-titulo, .title', { timeout: 10000 }).should('be.visible')
    cy.url().should('match', /\/[^\s]+\/$/)
  })
})
