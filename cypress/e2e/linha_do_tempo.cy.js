describe('Teste E2E - Linha do Tempo', () => {
  it('Deve clicar em uma notícia, descer até a linha do tempo e clicar em uma notícia relacionada', () => {
    // Visitar a página inicial
    cy.visit('/')

    // Aguardar o carregamento e clicar em um card de notícia
    cy.get('.card.top, .card.side, .news-item, a[href*="/"][class*="card"]', { timeout: 10000 })
      .should('exist')
      .and('be.visible')
      .first()
      .click({ force: true })
    
    // Aguardar a página de detalhes carregar
    cy.url().should('match', /\/.+\/$/)
    cy.wait(1000)
    
    // Verificar se a seção de linha do tempo existe
    cy.get('.linha-tempo-wrapper', { timeout: 10000 }).should('exist')
    
    // Rolar até a seção de linha do tempo
    cy.get('.linha-tempo-wrapper').scrollIntoView({ duration: 1000 })
    cy.wait(500)
    
    // Verificar que existem cards de notícias na linha do tempo
    cy.get('.carrossel-card').should('exist')
    
    // Clicar no link do primeiro card da linha do tempo
    cy.get('.carrossel-link').first().click({ force: true })
    
    // Verificar que navegou para outra página de notícia
    cy.url().should('match', /\/.+\/$/)
    
    // Verificar que a nova página tem o título da notícia
    cy.get('.noticia-titulo, .title').should('exist').and('be.visible')
  })
})
