describe('Teste de Salvar Notícias', () => {
  it('Deve salvar uma notícia e visualizá-la na página de salvos', () => {
    // Limpa localStorage antes do teste
    cy.clearLocalStorage()

    // Visita a página inicial
    cy.visit('/')

    // Aguarda uma notícia estar visível na home
    cy.get('.card.top').should('be.visible')

    // Clica na primeira notícia para abrir os detalhes
    cy.get('.card.top').first().click()

    // Aguarda a página de detalhes carregar (URL será o slug da notícia)
    cy.url().should('not.equal', 'http://127.0.0.1:8000/')

    // Aguarda o botão de salvar estar visível
    cy.get('.compartilhar-btn.salvar-btn', { timeout: 10000 }).should('be.visible')

    // Verifica que o botão não está salvo inicialmente
    cy.get('.compartilhar-btn.salvar-btn').should('have.attr', 'aria-pressed', 'false')

    // Clica no botão de salvar
    cy.get('.compartilhar-btn.salvar-btn').click()

    // Verifica que o botão mudou para salvo
    cy.get('.compartilhar-btn.salvar-btn').should('have.attr', 'aria-pressed', 'true')

    // Verifica que foi salvo no localStorage
    cy.window().then((win) => {
      const salvas = JSON.parse(win.localStorage.getItem('noticiasSalvas') || '[]')
      expect(salvas.length).to.be.greaterThan(0)
    })

    // Abre o menu hamburguer
    cy.get('#menuHamburguer').click()

    // Aguarda o menu lateral ficar visível
    cy.get('#menuLateral').should('be.visible')

    // Clica no link "Notícias Salvas" no menu
    cy.contains('.menu-link', 'Notícias Salvas').click()

    // Aguarda a página de salvos carregar
    cy.url().should('include', '/salvos/')

    // Verifica que há notícias na lista de salvos
    cy.get('.news-item', { timeout: 10000 }).should('exist')

    // Verifica que há pelo menos uma notícia salva
    cy.get('.news-item').should('have.length.greaterThan', 0)
  })
})
