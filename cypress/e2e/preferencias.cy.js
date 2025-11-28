describe('Teste de Preferências de Conteúdo', () => {
  it('Deve selecionar preferências e verificar que foram aplicadas', () => {
    // Define resolução mobile (iPhone X)
    cy.viewport(375, 812)

    // Limpa cookies e localStorage
    cy.clearCookies()
    cy.clearLocalStorage()

    // Visita a página inicial
    cy.visit('/')

    // Abre o menu hamburguer
    cy.get('#menuHamburguer').click()

    // Aguarda o menu lateral ficar visível
    cy.get('#menuLateral').should('be.visible')

    // Clica no botão de preferências
    cy.get('#btnAbrirPreferencias').click()

    // Aguarda o modal de preferências abrir
    cy.get('#modalPreferencias').should('be.visible')

    // Seleciona a categoria "Pernambuco"
    cy.get('.categoria-checkbox input[value="pernambuco"]').check()

    // Verifica que foi marcada
    cy.get('.categoria-checkbox input[value="pernambuco"]').should('be.checked')

    // Clica no botão de salvar preferências
    cy.get('#btnSalvarPreferencias').click()

    // Aguarda a página recarregar
    cy.wait(1000)

    // Verifica que a barra de preferências ativas está visível
    cy.get('#barraPreferenciasAtivas', { timeout: 10000 }).should('be.visible')
  })
})
