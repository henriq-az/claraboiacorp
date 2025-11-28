describe('Teste de Feedback', () => {
  it('Deve enviar um feedback a partir do menu hamburguer', () => {
    // Define resolução mobile (iPhone X)
    cy.viewport(375, 812)

    cy.visit('/')
    cy.get('#menuHamburguer').click()
    cy.get('.btn-feedback-menu').click()
    cy.get('label[for="nivel5"]').click()
    cy.get('#comentario').type('Este é um comentário de teste para avaliar a funcionalidade do feedback.')
    cy.get('.btn-enviar-feedback').click()
  })
})