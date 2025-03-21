// Script para gerenciar funcionalidades da página de campeonatos
$(document).ready(function() {
    console.log("Inicializando script de campeonatos");

    // Determinar em qual página estamos
    var isCreationPage = window.location.href.indexOf('campeonato/novo') !== -1 || 
                         window.location.href.indexOf('campeonato_novo') !== -1;
    var isListingPage = window.location.pathname.endsWith('/campeonatos/');
    
    console.log("Página atual: " + (isCreationPage ? "Criação" : (isListingPage ? "Listagem" : "Outra")));

    // Na página de criação
    if (isCreationPage) {
        // Configurar o botão salvar apenas para submissão básica
        $('#btn-salvar').on('click', function(e) {
            console.log("Botão salvar clicado");
            // Não precisamos fazer nada especial aqui
            // O toastr-override.js já configura este botão apropriadamente
        });
        
        // Configurar o botão cancelar para limpar cookies
        $('#btn-cancelar').on('click', function() {
            console.log("Botão cancelar clicado");
            // Limpar qualquer cookie existente ao cancelar
            document.cookie = 'campeonato_criado=; max-age=0; path=/;';
        });
        
        // Limpar cookies ao carregar a página
        document.cookie = 'campeonato_criado=; max-age=0; path=/;';
        
        console.log("Página de criação configurada");
    }
    
    // Configuração adicional para a página de listagem
    if (isListingPage) {
        console.log("Configurando página de listagem");
        
        // Se acabamos de ser redirecionados de uma criação bem-sucedida,
        // a mensagem já deve ter sido exibida pelo toastr-override.js
    }
}); 