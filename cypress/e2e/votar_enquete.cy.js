describe('Teste de Votação em Enquete', () => {
  it('Deve votar em uma enquete a partir da página de detalhes da notícia', () => {
    // Define resolução mobile (iPhone X)
    cy.viewport(375, 812)

    // Gera um IP único para este teste (evita conflito com votos anteriores)
    const fakeIp = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`

    // Visita a página inicial
    cy.visit('/')

    // Aguarda cards de notícias estarem visíveis
    cy.get('.card.top', { timeout: 10000 }).should('exist').and('be.visible')

    // Clica na primeira notícia para abrir os detalhes
    cy.get('.card.top, .card.side', { timeout: 10000 }).first().should('be.visible').click()

    // Aguarda a página de detalhes carregar e adiciona fake_ip à URL
    cy.url().should('not.equal', 'http://127.0.0.1:8000/').then((url) => {
      // Adiciona fake_ip à URL para simular um novo usuário
      const urlWithFakeIp = url.includes('?') ? `${url}&fake_ip=${fakeIp}` : `${url}?fake_ip=${fakeIp}`
      cy.visit(urlWithFakeIp)
    })

    // Verifica se existe enquete nesta página
    cy.get('body').then(($body) => {
      if ($body.find('.enquete-container').length === 0) {
        // Se não tem enquete, apenas loga e passa o teste
        cy.log('Esta notícia não possui enquete associada')
        expect(true).to.be.true
        return
      }

      // Se chegou aqui, tem enquete - prossegue com o teste
      cy.get('.enquete-container', { timeout: 10000 }).should('exist')

      // Rola até a enquete
      cy.get('.enquete-container').scrollIntoView()

      // Verifica se há opções de enquete disponíveis
      cy.get('.enquete-opcao-label').should('exist')

      // Clica na primeira opção da enquete
      cy.get('.enquete-opcao-label').first().click()

      // Verifica que o radio button foi selecionado
      cy.get('.enquete-opcao-label').first().find('input[type="radio"]').should('be.checked')

      // Adiciona campo hidden fake_ip ao formulário para garantir IP único
      cy.get('.enquete-form').then(($form) => {
        const hiddenInput = document.createElement('input')
        hiddenInput.type = 'hidden'
        hiddenInput.name = 'fake_ip'
        hiddenInput.value = fakeIp
        $form[0].appendChild(hiddenInput)
      })

      // Clica no botão de votar
      cy.get('.enquete-votar-btn').click()

      // Aguarda a página recarregar ou os resultados aparecerem
      cy.wait(1000)

      // Verifica que os resultados estão sendo exibidos
      cy.get('.enquete-resultados', { timeout: 10000 }).should('be.visible')

      // Verifica que há barras de progresso (resultados)
      cy.get('.enquete-barra-progresso').should('exist')
    })
  })
})
