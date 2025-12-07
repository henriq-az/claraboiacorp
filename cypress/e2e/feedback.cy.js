describe('Teste de Feedback', () => {
  it('Deve enviar um feedback a partir do menu hamburguer', () => {
    // Define resolução mobile (iPhone X)
    cy.viewport(375, 812)

    // Visita a página e aguarda carregar
    cy.visit('/')
    cy.wait(1000)

    // Abre o menu hamburguer
    cy.get('#menuHamburguer', { timeout: 10000 }).should('be.visible').click()

    // Aguarda o menu lateral aparecer
    cy.get('#menuLateral', { timeout: 5000 }).should('be.visible')

    // Clica no botão de feedback
    cy.get('.btn-feedback-menu', { timeout: 5000 }).should('exist').click()

    // Aguarda o modal de feedback aparecer
    cy.get('#modalFeedback, .modal-feedback', { timeout: 5000 }).should('be.visible')

    // Seleciona uma avaliação
    cy.get('label[for="nivel5"]', { timeout: 5000 }).should('exist').click()

    // Digite um comentário
    cy.get('#comentario', { timeout: 5000 }).should('be.visible').type('Este é um comentário de teste para avaliar a funcionalidade do feedback.')

    // Clica no botão de enviar
    cy.get('.btn-enviar-feedback', { timeout: 5000 }).should('be.visible').click()

    // Aguarda a resposta
    cy.wait(1000)
  })
})