describe('Teste de Compartilhamento de Notícias', () => {
  it('Deve compartilhar uma notícia a partir da página de detalhes', () => {
    // Define resolução mobile (iPhone X)
    cy.viewport(375, 812)

    // Visita a página inicial
    cy.visit('/')

    // Aguarda cards de notícias estarem visíveis (tenta múltiplos seletores)
    cy.get('.card.top, .card.side, .news-item, a[href*="/"][class*="card"]', { timeout: 10000 })
      .should('exist')
      .and('be.visible')
      .first()
      .click()

    // Aguarda a página de detalhes carregar (URL será o slug da notícia)
    cy.url().should('not.equal', 'http://127.0.0.1:8000/')

    // Configura o stub do clipboard na janela atual
    cy.window().then((win) => {
      cy.stub(win.navigator.clipboard, 'writeText').resolves().as('clipboardWriteText')
    })

    // Aguarda o botão de compartilhar estar visível
    cy.get('button[aria-label="Compartilhar"]', { timeout: 10000 }).should('be.visible')

    // Clica no botão de compartilhar
    cy.get('button[aria-label="Compartilhar"]').click()

    // Verifica que a função de clipboard foi chamada
    cy.get('@clipboardWriteText').should('have.been.called')
  })
})
