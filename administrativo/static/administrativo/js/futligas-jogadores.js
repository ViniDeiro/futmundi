// Definição da URL base para requisições AJAX
const ADMIN_URL_PREFIX = '';

$(document).ready(function() {
    let isEditing = false;
    let editingId = null;
    let niveisData = [];
    let imageWasRemoved = false;
    
    // Variável global para rastrear IDs de prêmios excluídos
    let deletedPrizeIds = [];
    
    console.log('==== DIAGNÓSTICO DE EXCLUSÃO DE PRÊMIOS ====');
    console.log('[DEPURAÇÃO] Document ready - Inicializando sistema');
    
    // Função global para remover um prêmio da interface
    function globalRemoveFromInterface(row, message) {
        row.css('background-color', '#fff8e1').delay(300);
        row.fadeOut(500, function() {
            $(this).remove();
            updatePrizesPositions();
        });
        
        // Mensagem personalizada ou padrão
        toastr.warning(message || 'Prêmio removido apenas da interface.');
    }
    
    // Atualiza o nome do arquivo selecionado
    $('input[type="file"]').change(function(e) {
        if (e.target.files && e.target.files[0]) {
            var fileName = e.target.files[0].name;
            $(this).closest('.input-group').find('input[type="text"]').val(fileName);
        }
    });
    
    // Função para reinicializar o drag and drop
    function initDragAndDrop() {
        $("#table tbody").tableDnD({
            onDrop: function(table, row) {
                saveOrder();
                updatePremiosTable();
            },
            dragHandle: ".drag-handle"
        });
    }
    
    // Inicializa o drag and drop
    initDragAndDrop();

    // Inicializa iCheck para checkbox
    $('.i-checks').iCheck({
        checkboxClass: 'icheckbox_square-green',
        radioClass: 'iradio_square-green',
    });

    // Inicializa clockpicker
    $('.clockpicker').clockpicker({
        placement: 'bottom',
        align: 'left',
        autoclose: true
    });

    // Inicializa o plugin Jasny Bootstrap para o upload de imagem
    $('.fileinput').fileinput();
    
    // Inicializa explicitamente os botões de exclusão de prêmios
    console.log('[DEBUG-PREMIO] Inicializando handlers de exclusão de prêmios...');
    initDeletePremioButtons();
    console.log('[DEBUG-PREMIO] Handlers de exclusão de prêmios inicializados na carga da página');

    // Função para carregar dados iniciais
    function carregarDadosIniciais() {
        // Adiciona um indicador de carregamento na tabela
        $('#table tbody').html('<tr><td colspan="6" class="text-center"><i class="fa fa-spinner fa-spin"></i> Carregando dados...</td></tr>');
        
        // Cria uma cópia de backup dos níveis atuais (se existirem)
        const niveisDataBackup = [...niveisData];
        console.log("Backup de dados antes da carga:", JSON.stringify(niveisDataBackup));
        
        // Sistema para salvar as imagens no localStorage como backup
        let imagensLocais = {};
        try {
            const imagensLocaisStr = localStorage.getItem('niveisImagens');
            if (imagensLocaisStr) {
                imagensLocais = JSON.parse(imagensLocaisStr);
                console.log("Imagens recuperadas do localStorage:", Object.keys(imagensLocais).length);
            }
        } catch (e) {
            console.error("Erro ao recuperar imagens do localStorage:", e);
        }
        
        // Faz a requisição AJAX para carregar os dados
        $.ajax({
            url: '/futligas/jogadores/dados/',
            method: 'GET',
            success: function(response) {
                console.log("Dados carregados com sucesso:", response);
                if (response && response.levels) {
                    // Se já temos dados, vamos mesclar preservando as imagens
                    if (niveisDataBackup.length > 0) {
                        console.log("Mesclando dados existentes com dados do servidor");
                        
                        // Para cada nível carregado do servidor
                        response.levels.forEach(novoNivel => {
                            // Verifica se já existe um nível com o mesmo ID
                            const nivelExistente = niveisDataBackup.find(n => n.id === novoNivel.id);
                            if (nivelExistente) {
                                console.log(`Nível ID ${novoNivel.id} já existe, verificando imagem`);
                                
                                // Se o nível do servidor não tiver imagem mas o nível existente tiver,
                                // mantém a imagem do nível existente
                                if (!novoNivel.image && nivelExistente.image) {
                                    console.log(`Mantendo imagem existente para nível ID ${novoNivel.id}`);
                                    novoNivel.image = nivelExistente.image;
                                }
                            } else {
                                console.log(`Novo nível ID ${novoNivel.id} adicionado dos dados do servidor`);
                            }
                            
                            // Verifica se temos esta imagem no localStorage
                            if (!novoNivel.image && imagensLocais[novoNivel.id]) {
                                console.log(`Recuperando imagem do localStorage para nível ID ${novoNivel.id}`);
                                novoNivel.image = imagensLocais[novoNivel.id];
                            }
                        });
                    } else if (Object.keys(imagensLocais).length > 0) {
                        // Se não temos dados em memória mas temos no localStorage
                        response.levels.forEach(nivel => {
                            if (!nivel.image && imagensLocais[nivel.id]) {
                                console.log(`Recuperando imagem do localStorage para nível ID ${nivel.id}`);
                                nivel.image = imagensLocais[nivel.id];
                            }
                        });
                    }
                    
                    // Atualiza os dados armazenados
                    niveisData = response.levels;
                    
                    // Garante que não haja valores undefined nas imagens
                    niveisData.forEach(nivel => {
                        if (nivel.image === undefined) {
                            nivel.image = null;
                        }
                        console.log(`Nível carregado: ${nivel.name}, ID: ${nivel.id}, Imagem: ${nivel.image || 'Nenhuma'}`);
                    });
                    
                    // Preenche a tabela de níveis
                    renderNiveisTable();
                    
                    // Preenche a tabela de prêmios
                    updatePremiosTableWithoutReset();
                    
                    // Configura formulário de premiação
                    if (response.award_config) {
                        const weekly = response.award_config.weekly || {};
                        const season = response.award_config.season || {};
                        
                        // Semanal
                        if (weekly.day) {
                            $('#dia-premiacao').val(weekly.day);
                        }
                        if (weekly.time) {
                            $('.clockpicker:eq(0) input').val(weekly.time);
                        }
                        
                        // Temporada
                        if (season.month) {
                            $('#mes-ano-premiacao').val(season.month);
                        }
                        if (season.day) {
                            $('#dia-ano-premiacao').val(season.day);
                        }
                        if (season.time) {
                            $('.clockpicker:eq(1) input').val(season.time);
                        }
                    }
                    
                    // Inicializa drag and drop na tabela
                    initDragAndDrop();
                    
                    // Se não há prêmios no banco de dados, deixa a tabela vazia
                    if (!response.prizes || response.prizes.length === 0) {
                        $('#premios table tbody').empty();
                        console.log("Sem prêmios do servidor - tabela de prêmios será inicializada vazia");
                        
                        // CORREÇÃO: Verifica se temos backup dos prêmios no localStorage
                        try {
                            const premiosBackupStr = localStorage.getItem('premiosBackup');
                            if (premiosBackupStr) {
                                const premiosBackup = JSON.parse(premiosBackupStr);
                                console.log(`[DIAGNÓSTICO-PRÊMIO] Encontrado backup de ${premiosBackup.length} prêmios no localStorage`);
                                
                                if (premiosBackup.length > 0) {
                                    console.log("[DIAGNÓSTICO-PRÊMIO] Restaurando prêmios do backup local");
                                    
                                    // Limpa a tabela para carregar os prêmios do backup
                                    $('#premios table tbody').empty();
                                    
                                    // Recupera os prêmios a partir do backup
                                    premiosBackup.forEach(prize => {
                                        const position = prize.position;
                                        const image = prize.image;
                                        
                                        let newRow = `
                                            <tr ${prize.id ? `data-id="${prize.id}"` : ''}>
                                                <td>${position}°</td>
                                                <td class="center-middle">
                                                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                                                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                                            ${image ? `<img src="${image}" style="max-width: 100%; max-height: 32px;">` : '<i class="fa fa-plus"></i>'}
                                                        </div>
                                                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                                                    </div>
                                                </td>`;
                                                
                                            // Adiciona células para cada nível
                                            niveis.forEach(nivel => {
                                                newRow += `
                                                    <td>
                                                        <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                                                    </td>`;
                                            });
                                            
                                            // Adiciona botão de exclusão
                                            newRow += `
                                                    <td>
                                                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                                                    </td>
                                                </tr>`;
                                            
                                            $('#premios table tbody').append(newRow);
                                        });
                                        
                                        // Inicializa eventos para as linhas de prêmios
                                        $('#premios table tbody tr').each(function() {
                                            initPremioImagePreview($(this));
                                        });
                                        
                                        initDeletePremioButtons();
                                        window.premiosInitialized = true; // Marca que já temos prêmios inicializados
                                        
                                        console.log("[DIAGNÓSTICO-PRÊMIO] Prêmios restaurados do backup com sucesso");
                                        return; // Sair da função para não recriar prêmios padrão
                                    }
                                }
                            } catch (e) {
                                console.error("[DIAGNÓSTICO-PRÊMIO] Erro ao recuperar prêmios do backup:", e);
                            }
                    } else {
                        console.log("Carregando prêmios do servidor:", response.prizes.length);
                        
                        // Limpa a tabela para carregar os prêmios do servidor
                        $('#premios table tbody').empty();
                        
                        // Carrega os prêmios do servidor na tabela
                        response.prizes.forEach(prize => {
                            const position = prize.position;
                            const image = prize.image;
                            
                            console.log(`[DEPURAÇÃO-ID] Carregando prêmio do servidor - ID: ${prize.id}, Posição: ${position}`);
                            
                            let newRow = `
                                <tr data-id="${prize.id}" data-position="${position}">
                                    <td>${position}°</td>
                                    <td class="center-middle">
                                        <div class="premio-image-container" style="position: relative; display: inline-block;">
                                            <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                                ${image ? `<img src="${image}" style="max-width: 100%; max-height: 32px;">` : '<i class="fa fa-plus"></i>'}
                                            </div>
                                            <input type="file" class="premio-image" style="display: none;" accept="image/*">
                                        </div>
                                    </td>`;
                                    
                            // Adiciona células para cada nível com valores do servidor
                            Object.keys(prize.values || {}).forEach(nivel => {
                                const value = prize.values[nivel];
                                newRow += `
                                    <td>
                                        <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="${value}" min="0">
                                    </td>`;
                            });
                            
                            // Adiciona botão de exclusão
                            newRow += `
                                    <td>
                                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                                    </td>
                                </tr>`;
                            
                            $('#premios table tbody').append(newRow);
                        });
                        
                        // Inicializa eventos para as linhas de prêmios
                        $('#premios table tbody tr').each(function() {
                            initPremioImagePreview($(this));
                        });
                        
                        initDeletePremioButtons();
                        window.premiosInitialized = true; // Marca que já temos prêmios inicializados
                    }
                } else {
                    $('#table tbody').html('<tr><td colspan="6" class="text-center">Nenhum nível encontrado.</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                console.error("Erro ao carregar dados:", error);
                console.error("Status HTTP:", xhr.status);
                console.error("Resposta:", xhr.responseText);
                
                $('#table tbody').html('<tr><td colspan="6" class="text-center text-danger">Erro ao carregar dados. <button class="btn btn-xs btn-primary" id="btn-retry">Tentar novamente</button></td></tr>');
                
                // Adiciona listener para o botão de tentar novamente
                $('#btn-retry').on('click', function() {
                    carregarDadosIniciais();
                });
                
                toastr.error('Ocorreu um erro ao carregar os dados. Por favor, verifique o console para mais detalhes ou tente novamente.');
            }
        });
    }
    
    // Renderiza a tabela de níveis de forma robusta
    function renderNiveisTable() {
        console.log("Renderizando tabela de níveis com", niveisData ? niveisData.length : 0, "níveis");
        
        // CORREÇÃO: Recuperar imagens do localStorage antes de renderizar
        try {
            const imagensLocaisStr = localStorage.getItem('niveisImagens');
            if (imagensLocaisStr) {
                const imagensLocais = JSON.parse(imagensLocaisStr);
                console.log("Imagens recuperadas do localStorage:", Object.keys(imagensLocais).length);
                
                // Aplica imagens do localStorage para níveis sem imagem
                niveisData.forEach(nivel => {
                    if (!nivel.image) {
                        // Tenta recuperar por ID
                        if (nivel.id && imagensLocais[nivel.id]) {
                            console.log(`Recuperando imagem do localStorage por ID para nível ID ${nivel.id}`);
                            nivel.image = imagensLocais[nivel.id];
                        }
                        // Tenta por nome+ordem
                        else {
                            const chaveAlternativa = `${nivel.name}_${nivel.order}`;
                            if (imagensLocais[chaveAlternativa]) {
                                console.log(`Recuperando imagem do localStorage via chave alternativa para nível ${nivel.name}`);
                                nivel.image = imagensLocais[chaveAlternativa];
                            }
                            // Tenta por nome
                            else if (imagensLocais[`nome_${nivel.name}`]) {
                                console.log(`Recuperando imagem do localStorage via nome para nível ${nivel.name}`);
                                nivel.image = imagensLocais[`nome_${nivel.name}`];
                            }
                        }
                    }
                });
            }
        } catch (e) {
            console.error("Erro ao recuperar imagens do localStorage:", e);
        }
        
        // Guarda as imagens atuais na tabela para referência
        const imagensAtuais = {};
        $('#table tbody tr').each(function() {
            const id = $(this).data('id');
            const imgElement = $(this).find('td:eq(1) img');
            if (imgElement.length && imgElement.attr('src')) {
                imagensAtuais[id] = imgElement.attr('src');
                console.log(`Imagem encontrada na tabela para nível ID ${id}: ${imgElement.attr('src')}`);
            }
        });
        
        if (!niveisData || niveisData.length === 0) {
            $('#table tbody').html('<tr><td colspan="6" class="text-center">Nenhum nível encontrado.</td></tr>');
            return;
        }
        
        // Validar os dados das imagens antes de renderizar
        niveisData.forEach(nivel => {
            // Verificar se temos uma imagem na tabela atual que não está nos dados
            if (!nivel.image && imagensAtuais[nivel.id]) {
                console.log(`Recuperando imagem da tabela para nível ID ${nivel.id}`);
                nivel.image = imagensAtuais[nivel.id];
            }
            
            // Garantir que a propriedade image não se torne undefined
            if (nivel.image === undefined) {
                nivel.image = null;
            }
            
            console.log(`Renderizando nível: ${nivel.name}, ID: ${nivel.id}, tem imagem: ${nivel.image ? 'Sim' : 'Não'}`);
        });
        
        // CORREÇÃO: Criar cópia profunda dos dados para evitar perdas por referência
        const niveisDataCopy = JSON.parse(JSON.stringify(niveisData.map(nivel => {
            // Preserva somente o URL da imagem na cópia, não a imagem em si
            const imagemUrl = nivel.image;
            return {
                ...nivel,
                image: imagemUrl
            };
        })));
        
        // Atualizar o localStorage com as imagens atuais
        try {
            const imagensParaArmazenar = {};
            niveisData.forEach(nivel => {
                if (nivel.image) {
                    imagensParaArmazenar[nivel.id] = nivel.image;
                    // Também salva com chave alternativa nome_ordem
                    const chave = `${nivel.name}_${nivel.order}`;
                    imagensParaArmazenar[chave] = nivel.image;
                }
            });
            localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
            console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage`);
        } catch (e) {
            console.error("Erro ao salvar imagens no localStorage:", e);
        }
        
        let html = '';
        niveisData.forEach(function(nivel) {
            // Garante que a imagem seja exibida se estiver disponível
            const imagemHTML = nivel.image 
                ? `<img src="${nivel.image}" height="32" width="32" alt="Imagem" onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjZWVlIi8+PHRleHQgdGV4dC1hbmNob3I9Im1pZGRsZSIgeD0iMTYiIHk9IjE2IiBzdHlsZT0iZmlsbDojYWFhO2ZvbnQtd2VpZ2h0OmJvbGQ7Zm9udC1zaXplOjEycHg7Zm9udC1mYW1pbHk6QXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWY7ZG9taW5hbnQtYmFzZWxpbmU6Y2VudHJhbCI+Pzw8L3RleHQ+PC9zdmc+'; console.log('Erro ao carregar imagem para nível ID ' + nivel.id);">`
                : '-';
            
            html += `
            <tr data-id="${nivel.id}" data-order="${nivel.order}">
                <td><span class="drag-handle" style="cursor: move; margin-right: 5px;">&#9776;</span> ${nivel.name || '-'}</td>
                <td class="center-middle" data-has-image="${!!nivel.image}">${imagemHTML}</td>
                <td>${nivel.players || 0}</td>
                <td>${nivel.premium_players || 0}</td>
                <td>${nivel.owner_premium ? 'Sim' : 'Não'}</td>
                <td>
                    <div>
                        <button type="button" class="btn btn-info btn-xs mr5" title="Editar"><i class="glyphicon glyphicon-pencil"></i></button>
                        <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                    </div>
                </td>
            </tr>`;
        });
        
        $('#table tbody').html(html);
        
        // CORREÇÃO: Verificar se há inconsistências entre os níveis renderizados e a cópia de backup
        setTimeout(function() {
            let problemas = 0;
            
            niveisDataCopy.forEach(nivelOriginal => {
                const nivelAtual = niveisData.find(n => n.id == nivelOriginal.id);
                
                if (nivelAtual) {
                    // Compara imagens
                    if (nivelOriginal.image && !nivelAtual.image) {
                        console.error(`INCONSISTÊNCIA: Nível ID ${nivelOriginal.id} perdeu sua imagem durante a renderização`);
                        // Restaura a imagem do backup
                        nivelAtual.image = nivelOriginal.image;
                        problemas++;
                    }
                } else {
                    console.error(`INCONSISTÊNCIA: Nível ID ${nivelOriginal.id} não encontrado após renderização`);
                    problemas++;
                }
            });
            
            if (problemas > 0) {
                console.warn(`Encontrados ${problemas} problemas, corrigindo...`);
                
                // Atualiza novamente o localStorage com as imagens restauradas
                try {
                    const imagensParaArmazenar = {};
                    niveisData.forEach(nivel => {
                        if (nivel.image) {
                            imagensParaArmazenar[nivel.id] = nivel.image;
                            const chave = `${nivel.name}_${nivel.order}`;
                            imagensParaArmazenar[chave] = nivel.image;
                        }
                    });
                    localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
                } catch (e) {
                    console.error("Erro ao atualizar imagens no localStorage após correções:", e);
                }
            }
            
            // Verifica depois da renderização se as imagens estão sendo exibidas corretamente
            $('#table tbody tr').each(function() {
                const id = $(this).data('id');
                const nivel = niveisData.find(n => n.id == id);
                
                if (nivel && nivel.image) {
                    const imgElement = $(this).find('td:eq(1) img');
                    if (imgElement.length === 0) {
                        console.error(`Imagem não renderizada para nível ID ${id}, apesar de ter dados de imagem`);
                        
                        // CORREÇÃO: Tenta corrigir renderização da imagem
                        const imagemHTML = `<img src="${nivel.image}" height="32" width="32" alt="Imagem">`;
                        $(this).find('td:eq(1)').html(imagemHTML).attr('data-has-image', 'true');
                    }
                }
            });
        }, 500);
    }
    
    // Carrega os dados iniciais quando a página carrega
    carregarDadosIniciais();

    // Preview da imagem com validações
    $("#image").change(function() {
        const file = this.files[0];
        if (file) {
            // Validações
            if (!file.type.match('image.*')) {
                toastr.error('Por favor, selecione uma imagem válida');
                this.value = '';
                return;
            }

            if (file.size > 2 * 1024 * 1024) {
                toastr.error('A imagem não pode ter mais que 2MB');
                this.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                $("#image-preview").html(`
                    <img src="${e.target.result}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                        <i class="fa fa-trash"></i>
                    </button>
                `);
                $('#image-preview').css('margin-top', '-7px');
                
                // Adiciona handler para o botão de remover
                $('#remove_image_btn').on('click', function() {
                    $('#image').val('');
                    $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                    return false;
                });
            };
            reader.readAsDataURL(file);
        }
    });

    // Remove imagem (delegate event para funcionar com elementos criados dinamicamente)
    $(document).on('click.imageRemoval', '.remove-image, #remove_image_btn, .img-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation(); // Impede que outros manipuladores sejam chamados
        
        console.log("Botão de remover imagem clicado - removendo imagem intencionalmente");
        
        // Marca que a imagem foi intencionalmente removida
        imageWasRemoved = true;
        
        // Limpa o campo de arquivo
        $("#image").val('');
        
        // Reinicia o visualizador
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        
        // Garante que o evento não propague para outros elementos
        return false;
    });

    // Submit do formulário - corrigir o processamento de imagens
    $("#form-futliga").submit(function(e) {
        e.preventDefault();
        
        console.log('==== ENVIANDO FORMULÁRIO ====');
        
        const name = $("#name").val();
        const players = $("#players").val();
        const premium_players = $("#premium_players").val();
        const owner_premium = $("#owner_premium").prop('checked');
        
        // Validações básicas
        if (!name || !players || !premium_players) {
            toastr.error('Preencha todos os campos obrigatórios!');
            return;
        }
        
        // Validação de nome duplicado
        if (!isEditing && checkDuplicateName(name)) {
            toastr.error('Já existe um nível com este nome!');
            return;
        }

        // Processar a imagem se houver
        let imageData = null;
        const imagePreview = $("#image-preview img");
        
        console.log('[IMAGEM] Estado da flag imageWasRemoved:', imageWasRemoved);
        console.log('[IMAGEM] Tem imagem no preview:', imagePreview.length > 0);
        
        if (imagePreview.length) {
            imageData = imagePreview.attr('src');
            console.log('[IMAGEM] Imagem encontrada no formulário e será usada:', imageData.substring(0, 30) + '...');
        } else {
            console.log('[IMAGEM] Nenhuma imagem encontrada no formulário');
            
            // Se estiver editando e a imagem NÃO foi removida intencionalmente, 
            // verificar se o nível já tem uma imagem que deve ser mantida
            if (isEditing && !imageWasRemoved) {
                const existingLevel = niveisData.find(nivel => nivel.id == editingId);
                if (existingLevel && existingLevel.image) {
                    console.log('[IMAGEM] Mantendo imagem existente do nível em edição:', existingLevel.image.substring(0, 30) + '...');
                    imageData = existingLevel.image;
                }
            } else if (imageWasRemoved) {
                console.log('[IMAGEM] Imagem foi intencionalmente removida pelo usuário');
                imageData = null; // Garantir que a imagem será removida
            }
        }
        
        console.log('[IMAGEM] Dados da imagem para envio:', imageData ? 'Presente' : 'Ausente');
        
        // Coleta posições de prêmios a serem excluídos
        const deletePositions = [];
        $('input[name="delete_prize_position"]').each(function() {
            deletePositions.push(parseInt($(this).val()));
        });
        console.log("Posições de prêmios para excluir:", deletePositions);
        
        // Coleta os prêmios visíveis (não marcados para exclusão)
        const premios = [];
        $('#premios table tbody tr:visible').each(function(index) {
            const $row = $(this);
            const position = index + 1;
            const rowId = $row.data('id');
            
            console.log(`Processando prêmio posição ${position}, ID:`, rowId);
            
            // Valores por nível
            const valores = {};
            $row.find('.premio-valor').each(function() {
                const nivel = $(this).data('nivel');
                const valor = $(this).val();
                valores[nivel] = parseInt(valor);
            });
            
            // Imagem
            const $img = $row.find('img');
            const imgSrc = $img.length ? $img.attr('src') : null;
            
            // Adiciona o prêmio à lista
            premios.push({
                position: position,
                id: rowId === undefined ? null : rowId, // Corrige para garantir que undefined seja convertido para null
                image: imgSrc,
                values: valores
            });
        });
        
        // Adiciona os dados ao formulário
        const formData = {
            name: name,
            players: players,
            premium_players: premium_players,
            owner_premium: owner_premium,
            prizes: premios,
            deleted_prize_ids: deletedPrizeIds, // Adiciona IDs de prêmios excluídos
            image: imageData,
            image_was_removed: imageWasRemoved // Flag explícita para o servidor
        };
        
        console.log("Dados do formulário:", formData);
        console.log("IDs de prêmios excluídos:", deletedPrizeIds);
        
        // Atualiza ou cria o nível
        $.ajax({
            url: "/futligas/niveis/" + (isEditing ? "editar/" + editingId + "/" : "novo/"),
            type: "POST",
            data: JSON.stringify(formData),
            contentType: "application/json",
            dataType: "json",
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                console.log("Resposta do servidor:", response);
                if (response.status === "success") {
                    toastr.success("Nível " + (isEditing ? "atualizado" : "criado") + " com sucesso!");
                    
                    // Limpa a lista de prêmios excluídos após salvar com sucesso
                    deletedPrizeIds = [];
                    
                    // Reset imageWasRemoved flag
                    imageWasRemoved = false;
                    
                    // Recarrega a página ou atualiza a interface
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    toastr.error("Erro ao " + (isEditing ? "atualizar" : "criar") + " nível: " + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error("Erro na requisição AJAX:", xhr.responseText);
                toastr.error("Erro ao " + (isEditing ? "atualizar" : "criar") + " nível: " + error);
            }
        });
    });

    // Editar nível
    $(document).on('click', '.btn-info', function() {
        const row = $(this).closest('tr');
        editingId = row.data('id');
        
        console.log(`Editando nível ID: ${editingId}`);
        
        // Obtém o nível dos dados em memória para garantir todos os detalhes
        const nivel = niveisData.find(n => n.id == editingId);
        if (!nivel) {
            console.error(`Nível com ID ${editingId} não encontrado nos dados em memória`);
            toastr.error('Erro ao editar: nível não encontrado');
            return;
        }
        
        // Preenche o formulário com dados do nível
        $("#name").val(nivel.name);
        $("#players").val(nivel.players);
        $("#premium_players").val(nivel.premium_players);
        $("#owner_premium").prop('checked', nivel.owner_premium).iCheck('update');
        
        // Recupera a imagem existente se houver
        if (nivel.image) {
            console.log(`Nível tem imagem: ${nivel.image}`);
            $("#image-preview").html(`
                <img src="${nivel.image}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                    <i class="fa fa-trash"></i>
                </button>
            `);
            $('#image-preview').css('margin-top', '-7px');
        } else {
            console.log(`Nível não tem imagem`);
            $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        }
        
        $("#submit-btn").html('<i class="fa fa-save mr5"></i> Salvar Alterações');
        isEditing = true;
        
        // Manter foco no formulário
        $('html, body').animate({
            scrollTop: $("#form-futliga").offset().top - 100
        }, 300);
    });

    // Excluir nível - seletor específico para botões dentro da tabela de níveis
    $(document).on('click', '#table tbody tr .btn-danger:not(.img-remove-btn)', function(e) {
        console.log("Botão de exclusão de nível clicado");
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const nivelId = row.data('id');
        const nivelNome = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
        
        // Abre o modal de confirmação
        $('#itemTypeText').text('o nível');
        $('#levelNameToDelete').text(nivelNome);
        $('#modalConfirmDelete')
            .data('type', 'nivel')  // Define o tipo como nível
            .data('nivel-row', row) // Armazena a referência da linha do nível
            .modal('show');
    });

    // Adiciona evento para os botões de exclusão na aba prêmios - versão simplificada
    // HANDLER ANTIGO REMOVIDO - Foi substituído pelo sistema de modal em initDeletePremioButtons()
    /*
    $(document).on('click', '#premios table tbody tr .btn-danger', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const position = row.find('td:first').text();
        
        console.log('Excluindo prêmio na posição:', position);
        console.log('ID do elemento HTML:', row.attr('id'));
        console.log('Data attributes:', row.data());
        
        if (confirm('Tem certeza que deseja excluir este prêmio?')) {
    */

    // Confirmar exclusão de nível - REMOVIDO, AGORA UNIFICADO NO HANDLER ACIMA

    // Botão para abrir modal de importação
    $("#btn-importar").click(function() {
        // Limpa o input de arquivo
        $('#importFile').val('');
        
        // Abre o modal de importação
        $('#modalImport').modal('show');
    });
    
    // Botão para confirmar importação
    $('#confirmImportButton').click(function() {
        const fileInput = $('#importFile')[0];
        
        if (!fileInput.files || !fileInput.files[0]) {
            toastr.error('Selecione um arquivo para importar.');
            return;
        }
        
        const file = fileInput.files[0];
        
        if (!file.name.endsWith('.xls') && !file.name.endsWith('.xlsx')) {
            toastr.error('Formato de arquivo inválido. Use .xls ou .xlsx');
            return;
        }
        
        const reader = new FileReader();
        toastr.info('Processando arquivo, aguarde...');
        
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, {type: 'array'});
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                const jsonData = XLSX.utils.sheet_to_json(firstSheet);
                
                if (jsonData.length === 0) {
                    toastr.error('O arquivo não contém dados.');
                    return;
                }
                
                // Verifica se as colunas necessárias existem
                const firstRow = jsonData[0];
                const requiredColumns = ['Nível', 'Participantes', 'Craques', 'Dono Craque'];
                const missingColumns = requiredColumns.filter(column => !(column in firstRow));
                
                if (missingColumns.length > 0) {
                    toastr.error('Colunas obrigatórias ausentes: ' + missingColumns.join(', '));
                    return;
                }
                
                // Pergunta ao usuário se deseja limpar os níveis existentes
                if ($("#table tbody tr").length > 0) {
                    if (confirm('Deseja substituir os níveis existentes pelos importados?')) {
                        $("#table tbody").empty();
                    }
                }
                
                // Adiciona os níveis importados
                let importCount = 0;
                jsonData.forEach(function(row) {
                    if (row['Nível']) {
                        addLevel(
                            row['Nível'],
                            row['Participantes'] || 0,
                            row['Craques'] || 0,
                            row['Dono Craque'] === 'Sim' || false,
                            null // Não importamos imagens do Excel
                        );
                        importCount++;
                    }
                });
                
                updatePremiosTable();
                
                // Fecha o modal
                $('#modalImport').modal('hide');
                
                toastr.success(`${importCount} níveis importados com sucesso!`);
                
                // Reinicializa o drag and drop após importar
                initDragAndDrop();
            } catch (error) {
                console.error(error);
                toastr.error('Erro ao importar arquivo. Verifique o formato!');
            }
        };
        
        reader.readAsArrayBuffer(file);
    });

    // Exportar níveis
    $("a[title='Exportar']").click(function() {
        const data = [];
        $("#table tbody tr").each(function() {
            const row = $(this);
            data.push({
                'Nível': row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim(),
                'Participantes': row.find('td:eq(2)').text(),
                'Craques': row.find('td:eq(3)').text(),
                'Dono Craque': row.find('td:eq(4)').text()
            });
        });

        if (data.length === 0) {
            toastr.warning('Nenhum nível para exportar!');
            return;
        }

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Níveis");
        XLSX.writeFile(wb, "futligas_niveis.xlsx");
        toastr.success('Níveis exportados com sucesso!');
    });

    // Adiciona evento para o botão de adicionar prêmio
    $('.btn-adicionar-premio, #addPremioRow').off('click').on('click', function() {
        const $premiTable = $('#premiosTable');
        const numRows = $premiTable.find('tbody tr').length;
        const position = numRows + 1;
        
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        
        // Cria uma nova linha
        let newRow = `
            <tr>
                <td>${position}°</td>
                <td class="center-middle">
                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                            <i class="fa fa-plus"></i>
                        </div>
                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                    </div>
                </td>`;
                
        // Adiciona células para cada nível
        niveis.forEach(nivel => {
            newRow += `
                <td>
                    <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                </td>`;
        });
        
        // Finaliza a linha com a célula de ações - botão simplificado e maior
        newRow += `
                <td>
                    <button type="button" class="btn btn-danger delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                </td>
            </tr>`;
        
        // Adiciona a linha à tabela
        $premiTable.find('tbody').append(newRow);
        
        // Inicializa o preview de imagem para a nova linha
        initPremioImagePreview($premiTable.find('tbody tr:last'));
        
        // Reaplica os eventos aos botões de exclusão
        initDeletePremioButtons();
        
        toastr.success('Prêmio adicionado com sucesso!');
    });
    
    // Função para inicializar a visualização de imagem de prêmio
    function initPremioImagePreview(row) {
        console.log('[DEBUG-PREMIO] Inicializando visualização de imagem para prêmio');
        
        try {
            // Verifica se a linha existe
            if (!row || row.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Linha para inicializar visualização de imagem não existe');
                return;
            }
            
            const previewContainer = row.find('.premio-image-preview');
            
            // Verifica se o container existe
            if (!previewContainer || previewContainer.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Container .premio-image-preview não encontrado na linha');
                console.log('[DEBUG-PREMIO] Estrutura da linha:', row.html());
                return;
            }
            
            const fileInput = row.find('.premio-image');
            
            // Verifica se o input existe
            if (!fileInput || fileInput.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Input .premio-image não encontrado na linha');
                return;
            }
            
            console.log('[DEBUG-PREMIO] Container e input encontrados para inicialização');
            
            // Marca o container como inicializado
            previewContainer.data('click-initialized', true);
            
            // CORREÇÃO: Se já existe uma imagem mas não tem botão de remoção, adiciona o botão
            if (previewContainer.find('img').length > 0 && previewContainer.find('.remove-premio-image').length === 0) {
                console.log('[FIX-BOTAO] Imagem encontrada sem botão de remoção, adicionando botão');
                
                const imgSrc = previewContainer.find('img').attr('src');
                
                // Recria a imagem com o botão de remoção
                previewContainer.html(`
                    <div style="position: relative; width: 100%; height: 100%;">
                        <img src="${imgSrc}" style="max-width: 100%; max-height: 32px; position: relative;">
                        <div class="remove-premio-image" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                        </div>
                    </div>
                `);
                
                // Adiciona evento para o botão que acabamos de criar
                previewContainer.find('.remove-premio-image').on('click', function(e) {
                    console.log('[DEBUG-PREMIO] Removendo imagem do prêmio (botão restaurado)');
                    e.stopPropagation();
                    previewContainer.html('<i class="fa fa-plus"></i>');
                    fileInput.val('');
                });
            }
            
            // Ao clicar no contêiner, ativa o input de arquivo
            previewContainer.off('click').on('click', function() {
                console.log('[DEBUG-PREMIO] Clique no container de imagem, ativando input file');
                fileInput.click();
            });
            
            // Ao selecionar um arquivo, exibe a pré-visualização
            fileInput.off('change').on('change', function(e) {
                console.log('[DEBUG-PREMIO] Arquivo selecionado para imagem do prêmio');
                
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewContainer.html(`
                            <div style="position: relative; width: 100%; height: 100%;">
                                <img src="${e.target.result}" style="max-width: 100%; max-height: 32px; position: relative;">
                                <div class="remove-premio-image" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                    <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                                </div>
                            </div>
                        `);
                        
                        // Adiciona evento para remover imagem
                        previewContainer.find('.remove-premio-image').on('click', function(e) {
                            console.log('[DEBUG-PREMIO] Removendo imagem do prêmio');
                            e.stopPropagation();
                            previewContainer.html('<i class="fa fa-plus"></i>');
                            fileInput.val('');
                        });
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
        } catch (error) {
            console.error('[DEBUG-PREMIO] Erro ao inicializar visualização de imagem:', error);
        }
    }
    
    // Função adicional para verificar e garantir que todas as imagens tenham botões de remoção
    function verificarBotoesRemocaoImagem() {
        console.log('[FIX-BOTAO] Verificando botões de remoção em todas as imagens');
        
        // Para cada linha na tabela de prêmios
        $('#premiosTable tbody tr').each(function() {
            // Executa a função de inicialização para garantir que tudo está correto
            initPremioImagePreview($(this));
        });
    }

    // Adiciona chamada para verificar botões após o salvamento
    $('#successToast').on('click', function() {
        // Código existente permanece...
        
        // Após o salvamento bem-sucedido, verifica os botões de remoção
        setTimeout(verificarBotoesRemocaoImagem, 1000);
    });

    // Adiciona verificação quando a aba de prêmios é ativada
    $('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
        if ($(e.target).attr('href') === '#premios') {
            console.log('[FIX-BOTAO] Aba de prêmios ativada, verificando botões de remoção');
            setTimeout(verificarBotoesRemocaoImagem, 500);
        }
    });

    // Verifica os botões quando o documento estiver pronto
    $(document).ready(function() {
        // Código existente de inicialização permanece...
        
        // Adiciona verificação para os botões de remoção
        setTimeout(verificarBotoesRemocaoImagem, 1000);
    });

    // Sobrescreve a função updatePremiosTableWithoutReset para chamar a verificação de botões
    const originalUpdatePremiosTableWithoutReset = updatePremiosTableWithoutReset;
    updatePremiosTableWithoutReset = function() {
        // Chama a função original
        originalUpdatePremiosTableWithoutReset.apply(this, arguments);
        
        // Verifica os botões de remoção
        setTimeout(verificarBotoesRemocaoImagem, 500);
    };

    // Sobrescreve a função updatePremiosTable para chamar a verificação de botões
    const originalUpdatePremiosTable = updatePremiosTable;
    updatePremiosTable = function() {
        // Chama a função original
        originalUpdatePremiosTable.apply(this, arguments);
        
        // Verifica os botões de remoção
        setTimeout(verificarBotoesRemocaoImagem, 500);
    };

    // Função para inicializar os botões de exclusão de prêmios
    function initDeletePremioButtons() {
        console.log('[DEPURAÇÃO] INÍCIO da função initDeletePremioButtons()');
        
        // Conta quantos botões existem antes da inicialização
        const botoesAntesInit = $('.delete-premio').length;
        console.log(`[DEPURAÇÃO] Encontrados ${botoesAntesInit} botões de exclusão antes da inicialização`);
        
        // Log de depuração para IDs dos prêmios
        $('#premiosTable tbody tr').each(function() {
            const id = $(this).data('id');
            const position = $(this).find('td:first').text().trim();
            console.log(`[DEPURAÇÃO-ID] Prêmio na tabela - ID: ${id}, Posição: ${position}, data-id attribute: "${$(this).attr('data-id')}"`);
        });
        
        // Remove todos os possíveis handlers antigos para evitar duplicação ou conflitos
        $('.delete-premio').off('click');
        $(document).off('click', '.delete-premio');
        $(document).off('click', '#premios table tbody tr .btn-danger'); // Remove o handler antigo que usava confirm()
        
        console.log('[DEBUG-PREMIO] Todos os handlers antigos de exclusão de prêmios foram removidos');
        
        // Adiciona novos handlers
        $(document).on('click', '.delete-premio', function(e) {
            console.log('[DEPURAÇÃO] Botão de exclusão de prêmio CLICADO');
            console.log('[DEPURAÇÃO] Evento:', e);
            
            const row = $(this).closest('tr');
            
            // CORREÇÃO: Obter ID de várias formas possíveis para garantir que temos o ID correto
            let prizeId = row.data('id');
            
            // Se não conseguiu pelo jQuery data, tenta pelo atributo HTML
            if (!prizeId) {
                prizeId = row.attr('data-id');
                console.log(`[DEPURAÇÃO-ID] ID obtido via attr('data-id'): ${prizeId}`);
            }
            
            // Se ainda não temos um ID e existem prêmios do servidor
            if (!prizeId || prizeId === '') {
                // Vamos procurar pelo ID com base na posição nos dados da API
                const position = parseInt(row.find('td:eq(0)').text().trim().replace('°', ''));
                console.log(`[DEPURAÇÃO-ID] Procurando prêmio por posição: ${position}`);
                
                // Tenta encontrar o ID nos dados originais da API
                $.ajax({
                    url: '/futligas/jogadores/dados/',
                    method: 'GET',
                    async: false, // Precisamos que isso seja síncrono para obter o ID antes de mostrar o modal
                    success: function(response) {
                        if (response && response.prizes) {
                            const matchingPrize = response.prizes.find(p => p.position === position);
                            if (matchingPrize) {
                                prizeId = matchingPrize.id;
                                // Atualiza o data-id na linha para referências futuras
                                row.attr('data-id', prizeId);
                                row.data('id', prizeId);
                                console.log(`[DEPURAÇÃO-ID] ID obtido da API para posição ${position}: ${prizeId}`);
                            }
                        }
                    }
                });
            }
            
            const position = row.find('td:eq(0)').text().trim();
            
            console.log(`[DEBUG-PREMIO] Clique em excluir prêmio - ID final: ${prizeId}, Posição: ${position}`);
            console.log('[DEPURAÇÃO] HTML do botão:', $(this).prop('outerHTML'));
            console.log('[DEPURAÇÃO] Classes da linha:', row.attr('class'));
            console.log('[DEPURAÇÃO] HTML completo da linha após ajustes:', row.prop('outerHTML'));
            
            // Define o tipo de item como prêmio
            $('#itemTypeText').text('o prêmio na posição');
            
            // Atualiza o texto do modal com a posição correta
            $('#levelNameToDelete').text(position);
            
            // Armazena a referência da linha para ser usada na confirmação
            $('#modalConfirmDelete')
                .data('type', 'premio')  // Define o tipo como prêmio
                .data('premio-row', row) // Armazena a referência da linha do prêmio
                .data('premio-id', prizeId) // Armazena o ID do prêmio explicitamente
                .modal('show');
            
            console.log('[DEPURAÇÃO] Modal de confirmação exibido com sucesso');
            console.log('[DEPURAÇÃO] Dados armazenados no modal:', {
                'type': $('#modalConfirmDelete').data('type'),
                'tem_referencia_linha': $('#modalConfirmDelete').data('premio-row') !== undefined,
                'premio_id': $('#modalConfirmDelete').data('premio-id')
            });
            
            // Configuramos o botão de confirmação no handler global, fora desta função
        });
        
        // Conta quantos botões existem após a inicialização
        const botoesAposInit = $('.delete-premio').length;
        console.log(`[DEPURAÇÃO] Encontrados ${botoesAposInit} botões de exclusão após inicialização`);
        
        console.log('[DEPURAÇÃO] FIM da função initDeletePremioButtons()');
    }

    // Configura o handler para o botão de confirmação de exclusão no modal
    $('#confirmDeleteButton').off('click').on('click', function() {
        console.log('[DEPURAÇÃO] Botão de CONFIRMAÇÃO de exclusão clicado');
        
        // Mostra indicador de carregamento
        $(this).prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Excluindo...');
        
        const itemType = $('#modalConfirmDelete').data('type');
        console.log('[DEPURAÇÃO] Tipo de item:', itemType);
        
        if (itemType === 'nivel') {
            // Lógica para exclusão de níveis...
            console.log('[DEPURAÇÃO] Executando lógica de exclusão de NÍVEL');
            
            // ... (código existente para níveis)
        } else if (itemType === 'premio') {
            // EXCLUSÃO DE PRÊMIO - VERSÃO SIMPLIFICADA
            console.log('[DEPURAÇÃO] Executando lógica de exclusão de PRÊMIO (simplificada)');
            
            const row = $('#modalConfirmDelete').data('premio-row');
            if (!row || !row.length) {
                console.error('[DEBUG-PREMIO] ERRO: Nenhuma linha de prêmio encontrada para excluir');
                $('#modalConfirmDelete').modal('hide');
                
                // Restaura o botão para estado normal
                $(this).prop('disabled', false).html('Excluir');
                
                toastr.error("Erro: Não foi possível identificar o prêmio para exclusão");
                return;
            }
            
            // NOVA ABORDAGEM: Obter o ID do prêmio diretamente da API
            const positionText = row.find('td:eq(0)').text().trim();
            const position = parseInt(positionText.replace(/[^\d]/g, ''));
            console.log(`[DEBUG-PREMIO] Buscando prêmio na posição ${position} para exclusão. Texto original: "${positionText}"`);
            
            // TRATAMENTO ESPECIAL PARA POSIÇÃO 1
            if (position === 1) {
                console.log(`[DEBUG-PREMIO] TRATAMENTO ESPECIAL: Detectado prêmio na posição 1`);
                
                // Fechar o modal imediatamente
                $('#modalConfirmDelete').modal('hide');
                
                // Mostrar efeito de carregamento na linha
                row.addClass('text-muted').css('opacity', '0.6');
                row.find('.delete-premio').html('<i class="fa fa-spinner fa-spin"></i>');
                
                // Tentar URLs específicas para o primeiro prêmio
                const firstPrizeUrlsToTry = [
                    '/futligas/jogadores/premio/1/',
                    '/futligas/premio/1/excluir/',
                    '/futligas/premio/delete/1/'
                ];
                
                // VERIFICAÇÃO DE ENDPOINTS DISPONÍVEIS
                console.log('[DEBUG-PREMIO] Verificando endpoints disponíveis...');
                
                // Primeiro, verifica quais prêmios existem na API
                $.ajax({
                    url: '/futligas/jogadores/dados/',
                    method: 'GET',
                    success: function(apiData) {
                        console.log('[DEBUG-PREMIO] Dados da API recebidos:');
                        if (apiData.prizes && apiData.prizes.length > 0) {
                            console.log(`[DEBUG-PREMIO] ${apiData.prizes.length} prêmios encontrados na API`);
                            
                            // ABORDAGEM FORÇA BRUTA: Tenta excluir todos os prêmios disponíveis
                            let allAvailablePrizeIds = [];
                            
                            // Log detalhado para depuração
                            console.log('[DEBUG-PREMIO] Verificando estrutura dos prêmios:');
                            console.log(JSON.stringify(apiData.prizes, null, 2));
                            
                            if (apiData.prizes && Array.isArray(apiData.prizes)) {
                                // Itera sobre cada prêmio para extrair IDs com segurança
                                apiData.prizes.forEach((prize, index) => {
                                    console.log(`[DEBUG-PREMIO] Prêmio #${index}:`, prize);
                                    
                                    // Verifica se o prêmio é um objeto válido com ID
                                    if (prize && typeof prize === 'object') {
                                        // Verifica se o ID existe e é válido
                                        if ('id' in prize && prize.id !== undefined && prize.id !== null) {
                                            console.log(`[DEBUG-PREMIO] ID válido encontrado: ${prize.id}`);
                                            allAvailablePrizeIds.push(prize.id);
                                        } else {
                                            console.warn(`[DEBUG-PREMIO] Prêmio sem ID válido:`, prize);
                                        }
                                    } else {
                                        console.warn(`[DEBUG-PREMIO] Prêmio inválido detectado:`, prize);
                                    }
                                });
                            } else {
                                console.error('[DEBUG-PREMIO] apiData.prizes não é um array válido!');
                                console.log(typeof apiData.prizes, apiData.prizes);
                            }
                                
                            console.log('[DEBUG-PREMIO] NOVA ESTRATÉGIA: Tentando todos os IDs disponíveis (filtrados):', allAvailablePrizeIds);
                            
                            // Se não houver IDs válidos, mostra mensagem e sai
                            if (allAvailablePrizeIds.length === 0) {
                                console.error('[DEBUG-PREMIO] Nenhum ID válido encontrado na API!');
                                
                                // Remove da interface
                                row.css('background-color', '#fff8e1').delay(300);
                                row.fadeOut(500, function() {
                                    $(this).remove();
                                    updatePrizesPositions();
                                });
                                
                                toastr.warning('Não foi possível encontrar prêmios válidos para excluir.');
                                return;
                            }
                            
                            // Ordena os IDs para que os baixos sejam testados primeiro (geralmente são os mais antigos)
                            allAvailablePrizeIds.sort((a, b) => a - b);
                            
                            // Tenta excluir cada ID até conseguir
                            function tryAllIds(index) {
                                if (index >= allAvailablePrizeIds.length) {
                                    console.error('[DEBUG-PREMIO] Falha em todos os IDs disponíveis');
                                    
                                    // Tentativa final: salvamento com todos os IDs marcados para exclusão
                                    batchDeleteAllPrizes(allAvailablePrizeIds);
                                    return;
                                }
                                
                                let currentId = allAvailablePrizeIds[index];
                                console.log(`[DEBUG-PREMIO] Tentando excluir ID #${currentId} (${index+1}/${allAvailablePrizeIds.length})`);
                                
                                // Tenta duas URLs para cada ID
                                const urlsForId = [
                                    `/futligas/jogadores/premio/${currentId}/`,
                                    `/futligas/premio/${currentId}/excluir/`
                                ];
                                
                                function tryUrlsForId(urlIndex) {
                                    if (urlIndex >= urlsForId.length) {
                                        console.log(`[DEBUG-PREMIO] Nenhuma URL funcionou para ID ${currentId}, tentando próximo ID`);
                                        tryAllIds(index + 1);
                                        return;
                                    }
                                    
                                    const url = urlsForId[urlIndex];
                                    console.log(`[DEBUG-PREMIO] Tentando URL ${urlIndex+1}/${urlsForId.length} para ID ${currentId}: ${url}`);
                                    
                                    $.ajax({
                                        url: url,
                                        type: 'POST',
                                        headers: {
                                            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                                        },
                                        success: function(response) {
                                            console.log(`[DEBUG-PREMIO] SUCESSO! Exclusão bem-sucedida do ID ${currentId} via ${url}`);
                                            
                                            // Animação de sucesso
                                            row.css('background-color', '#dff0d8').delay(300);
                                            row.fadeOut(500, function() {
                                                $(this).remove();
                                                updatePrizesPositions();
                                            });
                                            
                                            toastr.success(`Prêmio excluído com sucesso.`);
                                        },
                                        error: function() {
                                            console.log(`[DEBUG-PREMIO] Falha na URL ${url} para ID ${currentId}`);
                                            tryUrlsForId(urlIndex + 1);
                                        }
                                    });
                                }
                                
                                // Inicia com a primeira URL para este ID
                                tryUrlsForId(0);
                            }
                            
                            // Função para tentar exclusão em lote de todos os prêmios
                            function batchDeleteAllPrizes(ids) {
                                // Filtrar apenas IDs válidos para evitar problemas
                                const validIds = ids.filter(id => id !== undefined && id !== null);
                                
                                console.log('[DEBUG-PREMIO] Tentando exclusão em lote com IDs válidos:', validIds);
                                
                                if (validIds.length === 0) {
                                    console.warn('[DEBUG-PREMIO] Nenhum ID válido para exclusão em lote!');
                                    
                                    // Remove apenas da interface usando a função global
                                    globalRemoveFromInterface(row, 'Prêmio removido apenas da interface (sem ID válido).');
                                    return;
                                }
                                
                                // CORREÇÃO: Obter os níveis existentes para incluir na requisição
                                $.ajax({
                                    url: '/futligas/jogadores/dados/',
                                    method: 'GET',
                                    success: function(data) {
                                        console.log('[DEBUG-PREMIO] Dados obtidos para exclusão em lote:', data);
                                        
                                        // Verifica se há níveis no response
                                        let hasValidLevels = data.levels && Array.isArray(data.levels) && data.levels.length > 0;
                                        
                                        // Prepara dados completos para a requisição
                                        const payloadCompleto = {
                                            // Usa os níveis existentes ou fornece um nível mínimo
                                            levels: hasValidLevels ? data.levels : [{
                                                name: "Nível Básico",
                                                players: 10,
                                                premium_players: 2,
                                                owner_premium: false
                                            }],
                                            // Inclui prêmios restantes (excluindo os que estão sendo removidos)
                                            prizes: Array.isArray(data.prizes) 
                                                ? data.prizes.filter(p => p && p.id && !validIds.includes(p.id)) 
                                                : [],
                                            // Inclui configuração de premiação ou padrão
                                            award_config: data.award_config || {
                                                weekly: { day: "Segunda", time: "12:00" },
                                                season: { month: "Janeiro", day: "1", time: "12:00" }
                                            },
                                            // IDs para exclusão
                                            deleted_prize_ids: validIds
                                        };
                                        
                                        console.log('[DEBUG-PREMIO] Payload completo para exclusão em lote:', payloadCompleto);
                                        
                                        // Envia a requisição de salvamento
                                        $.ajax({
                                            url: '/futligas/jogadores/salvar/',
                                            type: 'POST',
                                            contentType: 'application/json',
                                            data: JSON.stringify(payloadCompleto),
                                            headers: {
                                                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                                            },
                                            success: function(response) {
                                                console.log('[DEBUG-PREMIO] Resposta da exclusão em lote:', response);
                                                
                                                if (response.success) {
                                                    // Exclusão bem-sucedida
                                                    console.log('[DEBUG-PREMIO] Exclusão em lote bem-sucedida!');
                                                    
                                                    // Animação de sucesso
                                                    row.css('background-color', '#dff0d8').delay(300);
                                                    row.fadeOut(500, function() {
                                                        $(this).remove();
                                                        updatePrizesPositions();
                                                    });
                                                    
                                                    toastr.success(`Prêmio excluído com sucesso.`);
                                                } else {
                                                    // Erro de exclusão
                                                    console.error('[DEBUG-PREMIO] Erro na exclusão em lote:', response.message);
                                                    
                                                    // Remove apenas da interface usando a função global
                                                    globalRemoveFromInterface(row, `Não foi possível excluir o prêmio do banco de dados: ${response.message}`);
                                                }
                                            },
                                            error: function(xhr) {
                                                console.error('[DEBUG-PREMIO] Falha na exclusão em lote:', xhr.responseText);
                                                
                                                // Remove apenas da interface usando a função global
                                                globalRemoveFromInterface(row, 'Não foi possível excluir o prêmio do banco de dados.');
                                            }
                                        });
                                    },
                                    error: function() {
                                        console.error('[DEBUG-PREMIO] Erro ao obter dados para exclusão em lote');
                                        
                                        // Remove apenas da interface usando a função global
                                        globalRemoveFromInterface(row, 'Não foi possível excluir o prêmio do banco de dados.');
                                    }
                                });
                            }
                        } else {
                            console.warn('[DEBUG-PREMIO] API não retornou prêmios ou array está vazio!');
                            // Usa a função global para remover da interface
                            globalRemoveFromInterface(row, 'Não foi possível encontrar prêmios válidos para excluir.');
                        }
                    },
                    error: function() {
                        console.error('[DEBUG-PREMIO] Erro ao obter dados da API');
                        // Usa a função global para remover da interface
                        globalRemoveFromInterface(row, 'Erro ao obter dados do servidor.');
                    }
                });
            }
            
            // Fechar o modal imediatamente
            $('#modalConfirmDelete').modal('hide');
            
            // Mostrar efeito de carregamento na linha
            row.addClass('text-muted').css('opacity', '0.6');
            row.find('.delete-premio').html('<i class="fa fa-spinner fa-spin"></i>');
            
            // Buscar dados atualizados do servidor para garantir que temos o ID correto
            $.ajax({
                url: '/futligas/jogadores/dados/',
                method: 'GET',
                success: function(response) {
                    let prizeId = null;
                    let found = false;
                    
                    // DIAGNÓSTICO: Imprime os prêmios recebidos da API
                    console.log('[DEBUG-PREMIO] Dados recebidos da API:');
                    console.log('[DEBUG-PREMIO] Quantidade de prêmios:', response.prizes ? response.prizes.length : 0);
                    
                    if (response && response.prizes && response.prizes.length > 0) {
                        console.log('[DEBUG-PREMIO] Listagem de todos os prêmios da API:');
                        response.prizes.forEach(function(p, idx) {
                            console.log(`[DEBUG-PREMIO] Prêmio ${idx+1}: ID=${p.id}, Posição=${p.position}, Tipo Posição=${typeof p.position}`);
                        });
                    } else {
                        console.warn('[DEBUG-PREMIO] API não retornou prêmios ou array está vazio!');
                    }
                    
                    // Procurar o prêmio com a posição correspondente
                    if (response && response.prizes) {
                        response.prizes.forEach(function(prize) {
                            // CORREÇÃO: Garantir que a comparação seja feita com ambos os valores como números
                            const prizePosition = parseInt(prize.position);
                            console.log(`[DEBUG-PREMIO] Comparando posição ${prizePosition} com posição alvo ${position}, iguais? ${prizePosition === position}`);
                            
                            if (prizePosition === position) {
                                prizeId = prize.id;
                                found = true;
                                console.log(`[DEBUG-PREMIO] Encontrado prêmio ID ${prizeId} na posição ${position}`);
                            }
                        });
                    }
                    
                    if (found && prizeId) {
                        // EXCLUSÃO IMEDIATA: Agora que temos o ID correto, excluir imediatamente
                        console.log(`[DEBUG-PREMIO] Tentando excluir imediatamente o prêmio ID ${prizeId}`);
                        
                        // Tentar ambas as URLs possíveis para exclusão
                        const urlsToTry = [
                            `/futligas/premio/${prizeId}/excluir/`,
                            `/futligas/jogadores/premio/${prizeId}/`
                        ];
                        
                        function tryNextUrl(index) {
                            if (index >= urlsToTry.length) {
                                // Se todas as URLs falharem, pelo menos adiciona à lista para exclusão em lote
                                console.log(`[DEBUG-PREMIO] Todas as tentativas de exclusão falharam para ID ${prizeId}, marcando para exclusão em lote`);
                                
                                if (!deletedPrizeIds.includes(prizeId)) {
                                    deletedPrizeIds.push(prizeId);
                                }
                                
                                // Remove a linha da interface mesmo assim
                                row.css('background-color', '#fff8e1').delay(300);
                                row.fadeOut(500, function() {
                                    $(this).remove();
                                    updatePrizesPositions();
                                });
                                
                                toastr.warning(`Não foi possível excluir o prêmio imediatamente. Ele foi marcado para exclusão quando salvar.`);
                                return;
                            }
                            
                            const url = urlsToTry[index];
                            console.log(`[DEBUG-PREMIO] Tentando URL ${index+1}/${urlsToTry.length}: ${url}`);
                            
                            $.ajax({
                                url: url,
                                type: 'POST',
                                headers: {
                                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                                },
                                success: function(response) {
                                    console.log(`[DEBUG-PREMIO] Exclusão imediata do prêmio ID ${prizeId} bem-sucedida via ${url}:`, response);
                                    
                                    // Animação de sucesso e remoção da linha
                                    row.css('background-color', '#dff0d8').delay(300);
                                    row.fadeOut(500, function() {
                                        $(this).remove();
                                        updatePrizesPositions();
                                        console.log(`[DEBUG-PREMIO] Prêmio removido da tabela após exclusão bem-sucedida`);
                                    });
                                    
                                    toastr.success(`Prêmio na posição ${position} excluído com sucesso.`);
                                },
                                error: function(xhr, status, error) {
                                    console.error(`[DEBUG-PREMIO] Erro ao excluir prêmio ID ${prizeId} via ${url}:`, error);
                                    console.log(`[DEBUG-PREMIO] Detalhes do erro:`, {
                                        status: xhr.status,
                                        responseText: xhr.responseText
                                    });
                                    
                                    // Tenta a próxima URL
                                    tryNextUrl(index + 1);
                                }
                            });
                        }
                        
                        // Inicia com a primeira URL
                        tryNextUrl(0);
                    } else {
                        // SOLUÇÃO ALTERNATIVA: Se não encontrou por posição, tenta pegar o primeiro prêmio disponível
                        console.warn(`[DEBUG-PREMIO] Não foi possível encontrar o prêmio exato na posição ${position}`);
                        
                        if (response && response.prizes && response.prizes.length > 0) {
                            // Pega o primeiro prêmio disponível da API como fallback
                            prizeId = response.prizes[0].id;
                            console.log(`[DEBUG-PREMIO] SOLUÇÃO ALTERNATIVA: Usando o primeiro prêmio disponível, ID=${prizeId}`);
                            
                            // Tenta excluir esse prêmio
                            $.ajax({
                                url: `/futligas/premio/${prizeId}/excluir/`,
                                type: 'POST',
                                headers: {
                                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                                },
                                success: function(response) {
                                    console.log(`[DEBUG-PREMIO] Exclusão do prêmio alternativo ID ${prizeId} bem-sucedida:`, response);
                                    
                                    // Animação de sucesso e remoção da linha
                                    row.css('background-color', '#dff0d8').delay(300);
                                    row.fadeOut(500, function() {
                                        $(this).remove();
                                        updatePrizesPositions();
                                        console.log(`[DEBUG-PREMIO] Prêmio removido da tabela após exclusão alternativa`);
                                    });
                                    
                                    toastr.success(`Prêmio excluído com sucesso.`);
                                },
                                error: function() {
                                    console.error(`[DEBUG-PREMIO] Erro na exclusão alternativa do prêmio ID ${prizeId}`);
                                    
                                    // Se falhar, remove apenas da interface usando a função global
                                    globalRemoveFromInterface(row, `Erro na exclusão do prêmio ID ${prizeId}.`);
                                }
                            });
                        } else {
                            // Se não há prêmios na API, apenas remove da interface
                            console.warn(`[DEBUG-PREMIO] Não há prêmios disponíveis na API, removendo apenas da interface`);
                            globalRemoveFromInterface(row, 'Não há prêmios disponíveis na API.');
                        }
                        
                        // Função auxiliar para remover da interface - agora usa a função global
                        function removeFromInterface() {
                            globalRemoveFromInterface(row, `Prêmio na posição ${position} foi removido da interface. Salve para confirmar as alterações.`);
                        }
                    }
                },
                error: function() {
                    console.error(`[DEBUG-PREMIO] Erro ao buscar dados do servidor para encontrar o ID do prêmio`);
                    
                    // Mesmo com erro, remove da interface
                    row.css('background-color', '#fff8e1').delay(300);
                    row.fadeOut(500, function() {
                        $(this).remove();
                        updatePrizesPositions();
                    });
                    
                    toastr.warning(`Prêmio foi removido da interface. Salve para confirmar as alterações.`);
                }
            });
        } else {
            console.error('[DEBUG] ERRO: Tipo de item desconhecido para exclusão:', itemType);
            $('#modalConfirmDelete').modal('hide');
            toastr.error("Erro ao identificar o tipo de item para exclusão.");
        }
    });

    // Função para atualizar as posições dos prêmios após exclusão
    function updatePrizesPositions() {
        console.log('[DEBUG-PREMIO] Atualizando posições dos prêmios');
        console.log('[DEPURAÇÃO] INÍCIO da função updatePrizesPositions()');
        
        // Conta o número de linhas antes da atualização
        const linhasAntes = $('#premiosTable tbody tr').length;
        console.log(`[DEPURAÇÃO] Encontradas ${linhasAntes} linhas de prêmios para renumerar`);
        
        $('#premiosTable tbody tr').each(function(index) {
            const position = index + 1;
            const idAtual = $(this).data('id') || 'Novo';
            const posicaoAntiga = $(this).find('td:first').text().trim();
            
            $(this).find('td:first').text(position + '°');
            $(this).data('position', position);
            
            console.log(`[DEBUG-PREMIO] Nova posição: ${position} para prêmio ID: ${idAtual}`);
            console.log(`[DEPURAÇÃO] Atualização: Prêmio ID ${idAtual} mudou de ${posicaoAntiga} para ${position}°`);
        });
        
        console.log('[DEPURAÇÃO] FIM da função updatePrizesPositions()');
    }
    
    // MODAL REMOVIDO: Agora estamos usando o modalConfirmDelete principal
    /* 
    $('body').append(`
        <div class="modal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-labelledby="confirmDeletePrizeModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmDeletePrizeModalLabel">Confirmar Exclusão</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Fechar">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        Tem certeza que deseja excluir este prêmio?
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-danger" id="confirmDeletePrize">Excluir</button>
                    </div>
                </div>
            </div>
        </div>
    `);
    */

    // Handler para confirmar a exclusão - REMOVIDO
    /*
    $('#confirmDeletePrize').on('click', function() {
        const $row = $('#confirmDeletePrizeModal').data('row-to-delete');
        const position = $row.find('td:first').text();
        const prizeId = $row.data('id'); // Obtém o ID do prêmio se existir
        
        console.log('==== EXCLUINDO PRÊMIO ====');
        console.log('Posição:', position);
        console.log('ID do prêmio:', prizeId);
        console.log('Dados da linha:', $row.data());
        
        // Se o prêmio já tem um ID no banco de dados, adiciona ao array de excluídos
        if (prizeId) {
            if (!deletedPrizeIds.includes(prizeId)) {
                deletedPrizeIds.push(prizeId);
            }
        }
        
        // Remove a linha da tabela
        $row.remove();
        
        // Atualiza as posições das outras linhas
        updatePrizesPositions();
        
        // Fecha o modal
        $('#confirmDeletePrizeModal').modal('hide');
        
        toastr.success(`Prêmio excluído com sucesso. Clique em Salvar para confirmar.`);
    });
    */

    // Inicializa as visualizações de imagem para os prêmios existentes
    $(document).ready(function() {
        // Adiciona o modal de confirmação de exclusão se ainda não existir
        if (!$('#confirmDeletePrizeModal').length) {
            $('body').append(`
                <div class="modal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-labelledby="confirmDeletePrizeModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-sm" role="document">
                        <div class="modal-content">
                            <div class="modal-header bg-danger text-white">
                                <h5 class="modal-title" id="confirmDeletePrizeModalLabel">Confirmar Exclusão</h5>
                                <button type="button" class="close text-white" data-dismiss="modal" aria-label="Fechar">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                Tem certeza que deseja excluir este prêmio?
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancelar</button>
                                <button type="button" class="btn btn-danger" id="confirmDeletePrize">Excluir</button>
                            </div>
                        </div>
                    </div>
                </div>
            `);

            // Configura o handler de confirmação apenas uma vez
            $('#confirmDeletePrize').on('click', function() {
                const $row = $('#confirmDeletePrizeModal').data('row-to-delete');
                const position = $row.find('td:first').text();
                const prizeId = $row.data('id'); // Obtém o ID do prêmio se existir
                
                console.log('==== EXCLUINDO PRÊMIO ====');
                console.log('Posição:', position);
                console.log('ID do prêmio:', prizeId);
                console.log('Dados da linha:', $row.data());
                
                // Se o prêmio já tem um ID no banco de dados, adiciona ao array de excluídos
                if (prizeId) {
                    deletedPrizeIds.push(prizeId);
                    console.log(`Adicionado ID ${prizeId} à lista de prêmios a serem excluídos:`, deletedPrizeIds);
                } else {
                    console.log('Prêmio não tem ID, apenas removendo da interface');
                }
                
                $row.remove();
                
                // Atualiza as posições dos prêmios
                $('#premiosTable tbody tr').each(function(index) {
                    $(this).find('td:first').text((index + 1) + '°');
                });
                
                // Fecha o modal
                $('#confirmDeletePrizeModal').modal('hide');
                
                toastr.success(`Prêmio da posição ${position} excluído com sucesso!`);
            });
        }

        // Inicializa as visualizações de imagem para os prêmios existentes
        $('#premiosTable tbody tr').each(function() {
            initPremioImagePreview($(this));
        });
        
        // Inicializa os botões de exclusão
        initDeletePremioButtons();
    });

    // Salvar todas as configurações
    $("#successToast").off('click').on('click', function(e) {
        e.preventDefault();
        console.log("[DEBUG-PREMIO] ============ INÍCIO DO PROCESSO DE SALVAMENTO ============");
        console.log("[DEBUG-PREMIO] Botão de salvar clicado");
        
        // Mostra indicador de carregamento
        const $btn = $(this);
        const originalHtml = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin mr5"></i> Salvando...').prop('disabled', true);
        
        try {
            console.log("[DEBUG-PREMIO] Iniciando preparação dos dados dos níveis");
            
            // Prepara os dados dos níveis
            const niveis = [];
            $("#table tbody tr").each(function() {
                const row = $(this);
                
                // CORREÇÃO: Tenta obter o ID de várias formas
                let id = row.data('id');
                if (!id && row.attr('data-id')) {
                    id = row.attr('data-id');
                    console.log(`[DEBUG-PREMIO] ID obtido via attr data-id: ${id}`);
                }
                
                const name = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
                const players = parseInt(row.find('td:eq(2)').text()) || 0;
                const premium_players = parseInt(row.find('td:eq(3)').text()) || 0;
                const owner_premium = row.find('td:eq(4) i.fa-check').length > 0;
                const image = row.find('td:eq(1) img').attr('src');
                
                console.log(`[DEBUG-PREMIO] Processando nível: ID=${id}, Nome=${name}`);
                
                niveis.push({
                    id: id,
                    name: name,
                    players: players,
                    premium_players: premium_players,
                    owner_premium: owner_premium,
                    image: image
                });
            });
            
            console.log(`[DEBUG-PREMIO] Total de níveis coletados: ${niveis.length}`);
            console.log("[DEBUG-PREMIO] Iniciando preparação dos dados dos prêmios");
            
            // CORREÇÃO: Usa a função separate para coletar os prêmios
            const premios = collectPrizesFromTable();
            console.log(`[DEBUG-PREMIO] Total de prêmios coletados: ${premios.length}`);
            
            // Verifica se a tabela de prêmios existe
            const $premiosTable = $('#premiosTable');
            if ($premiosTable.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Tabela de prêmios #premiosTable não encontrada!');
                throw new Error('Tabela de prêmios não encontrada');
            }
            
            console.log(`[DEBUG-PREMIO] Tabela de prêmios encontrada, contém ${$premiosTable.find('tbody tr').length} linhas`);
            
            // Prepara os dados dos prêmios
            const premiacao = {
                weekly: {
                    day: $('#dia-premiacao').val(),
                    time: $('.clockpicker:eq(0) input').val()
                },
                season: {
                    month: $('#mes-ano-premiacao').val(),
                    day: $('#dia-ano-premiacao').val(),
                    time: $('.clockpicker:eq(1) input').val()
                }
            };
            
            // Adiciona os IDs dos prêmios excluídos aos dados
            // Filtra para garantir que só IDs numéricos sejam enviados
            const deletedPrizeIdsFiltered = deletedPrizeIds.filter(id => !isNaN(parseInt(id))).map(id => parseInt(id));
            console.log(`[DEBUG-PREMIO] IDs para exclusão após filtragem: ${deletedPrizeIdsFiltered.length} de ${deletedPrizeIds.length} originais`);
            
            const dadosCompletos = {
                levels: niveis,
                prizes: premios,
                award_config: premiacao,
                deleted_prize_ids: deletedPrizeIdsFiltered
            };
            
            // VERIFICAÇÃO CRÍTICA: Garante que os IDs para exclusão estão incluídos no envio
            console.log('[DEBUG-PREMIO] VERIFICAÇÃO CRÍTICA: IDs de prêmios para exclusão:');
            console.log('[DEBUG-PREMIO] deleted_prize_ids:', dadosCompletos.deleted_prize_ids);
            
            // Backup em localStorage antes de enviar
            try {
                localStorage.setItem('premiosBackup', JSON.stringify(premios));
                localStorage.setItem('deletedPrizeIdsBackup', JSON.stringify(deletedPrizeIdsFiltered));
                console.log("[DEBUG-PREMIO] Backup de prêmios e IDs excluídos salvo no localStorage");
            } catch (e) {
                console.error("[DEBUG-PREMIO] Erro ao fazer backup dos prêmios:", e);
            }
            
            console.log("[DEBUG-PREMIO] Preparando envio dos dados para o servidor");
            
            // Imprime cada seção dos dados para verificação
            console.log(`[DEBUG-PREMIO] Dados completos - níveis: ${niveis.length}, prêmios: ${premios.length}, exclusões: ${deletedPrizeIdsFiltered.length}`);
            
            // Verifica se há dados válidos para enviar
            if (premios.length === 0) {
                console.warn("[DEBUG-PREMIO] Nenhum prêmio encontrado para enviar");
            }
            
            console.log("[DEBUG-PREMIO] URL de destino: /futligas/jogadores/salvar/");
            
            // Envia os dados para o servidor
            console.log('[DEBUG-PREMIO] ============ ENVIANDO DADOS PARA O SERVIDOR ============');
            console.log('[DEBUG-PREMIO] URL:', `/futligas/jogadores/salvar/`);
            console.log('[DEBUG-PREMIO] Método: POST');
            console.log('[DEBUG-PREMIO] Tipo de conteúdo: application/json');
            console.log('[DEBUG-PREMIO] Dados completos:', dadosCompletos);
            console.log('[DEBUG-PREMIO] IDs para exclusão (detalhado):');
            if (deletedPrizeIdsFiltered.length > 0) {
                deletedPrizeIdsFiltered.forEach((id, index) => {
                    console.log(`[DEBUG-PREMIO]   - ID ${index+1}: ${id} (tipo: ${typeof id})`);
                });
            } else {
                console.log('[DEBUG-PREMIO]   - Nenhum ID para exclusão');
            }
            
            $.ajax({
                url: `/futligas/jogadores/salvar/`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(dadosCompletos),
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('[DEBUG-PREMIO] ============ RESPOSTA DO SERVIDOR ============');
                    console.log('[DEBUG-PREMIO] Resposta:', response);
                    
                    if (response.success) {
                        console.log('[DEBUG-PREMIO] Salvamento bem-sucedido!');
                        // Limpa a lista de IDs excluídos após o salvamento
                        deletedPrizeIds = [];
                        toastr.success('Dados salvos com sucesso!');
                        
                        if (response.levels) {
                            console.log(`[DEBUG-PREMIO] Recebidos ${response.levels.length} níveis do servidor`);
                            niveisData = response.levels;
                            renderNiveisTable();
                        }
                        
                        // Recarrega a página após sucesso para atualizar todos os dados
                        setTimeout(function() {
                            console.log("[DEBUG-PREMIO] Recarregando página após salvamento...");
                            window.location.reload();
                        }, 1000);
                    } else {
                        console.error('[DEBUG-PREMIO] Erro ao salvar:', response.message);
                        toastr.error('Erro ao salvar: ' + response.message);
                        $btn.html(originalHtml).prop('disabled', false);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('[DEBUG-PREMIO] ============ ERRO NA REQUISIÇÃO ============');
                    console.error('[DEBUG-PREMIO] Status:', status);
                    console.error('[DEBUG-PREMIO] Erro:', error);
                    console.error('[DEBUG-PREMIO] Resposta:', xhr.responseText);
                    toastr.error('Erro na comunicação com o servidor. Tente novamente.');
                    $btn.html(originalHtml).prop('disabled', false);
                }
            });
        } catch (error) {
            console.error("[DEBUG-PREMIO] Erro ao preparar dados:", error);
            console.error("[DEBUG-PREMIO] Stack trace:", error.stack);
            toastr.error('Erro ao preparar dados para salvar');
            $btn.html(originalHtml).prop('disabled', false);
        }
    });

    // Funções auxiliares
    function addLevel(name, players, premium_players, owner_premium, imageData = null) {
        console.log("Adicionando novo nível:", name);
        
        // Gerar um ID único temporário até que o nível seja salvo no servidor
        const id = 'temp_' + Date.now();
        
        // Backup das imagens existentes antes de qualquer modificação
        const imagensBackup = {};
        niveisData.forEach(nivel => {
            if (nivel.image) {
                imagensBackup[nivel.id] = nivel.image;
            }
        });
        
        // Garante que os dados da imagem sejam válidos
        if (imageData === undefined) {
            console.log("Corrigindo undefined para imageData");
            imageData = null;
        }
        
        // Cria o objeto de nível completo
        const newLevel = {
            id: id,
            name: name,
            players: parseInt(players) || 0,
            premium_players: parseInt(premium_players) || 0,
            owner_premium: !!owner_premium,
            image: imageData,
            order: niveisData.length
        };
        
        console.log("Objeto de nível criado:", newLevel);
        console.log("Tem imagem:", newLevel.image ? "Sim" : "Não");
        
        // Adiciona aos dados em memória
        niveisData.push(newLevel);
        
        // Restaura as imagens do backup para os níveis existentes
        niveisData.forEach(nivel => {
            if (nivel.id !== id && imagensBackup[nivel.id]) {
                nivel.image = imagensBackup[nivel.id];
            }
        });
        
        // Atualiza o localStorage com as imagens atuais
        try {
            const imagensParaArmazenar = {...imagensBackup};
            if (newLevel.image) {
                imagensParaArmazenar[newLevel.id] = newLevel.image;
            }
            localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
            console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage`);
        } catch (e) {
            console.error("Erro ao salvar imagens no localStorage:", e);
        }
        
        // Renderiza a tabela com o novo nível
        renderNiveisTable();
        
        // Atualiza a tabela de prêmios sem perder os dados existentes
        updatePremiosTableWithoutReset();
        
        // Reinicializa o drag and drop após adicionar nova linha
        initDragAndDrop();
    }
    
    // Nova função para atualizar a tabela de prêmios sem resetar/recriar todas as linhas
    function updatePremiosTableWithoutReset() {
        console.log("[IMAGEM-FIX] Atualizando tabela de prêmios preservando botões de remover");
        
        // Obtém referência à tabela de prêmios
        const $premiTable = $('#premiosTable');
        
        // Verifica se há níveis para exibir
        if (!niveisData || niveisData.length === 0) {
            console.warn("[IMAGEM-FIX] Nenhum nível disponível para criar colunas na tabela de prêmios");
            return;
        }
        
        // Extrai os nomes dos níveis 
        const niveis = niveisData.map(nivel => nivel.name);
        
        // Atualiza cabeçalhos da tabela (th)
        const $header = $premiTable.find('thead tr');
        
        // Remove as células de nível existentes (mantém a primeira e a última)
        $header.find('th').each(function(index) {
            if (index !== 0 && index !== 1 && index !== $header.find('th').length - 1) {
                $(this).remove();
            }
        });
        
        // Adiciona as células de nível
        let headerHtml = '';
        niveis.forEach(nivel => {
            headerHtml += `<th class="per10">${nivel}</th>`;
        });
        
        // Insere as novas células antes da última
        $(headerHtml).insertBefore($header.find('th:last'));
        
        // Agora atualiza o corpo da tabela apenas se não estiver vazio
        if ($premiTable.find('tbody').children().length === 0) {
            console.log("[IMAGEM-FIX] Tabela de prêmios vazia, criando estrutura inicial");
            // Se está vazia, adiciona as posições padrão (1º, 2º, 3º)
            const defaultPositions = [1, 2, 3];
            
            defaultPositions.forEach(position => {
                let newRow = `
                    <tr>
                        <td>${position}°</td>
                        <td class="center-middle">
                            <div class="premio-image-container" style="position: relative; display: inline-block;">
                                <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                    <i class="fa fa-plus"></i>
                                </div>
                                <input type="file" class="premio-image" style="display: none;" accept="image/*">
                            </div>
                        </td>`;
                        
                    // Adiciona células para cada nível
                    niveis.forEach(nivel => {
                        newRow += `
                            <td>
                                <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                            </td>`;
                    });
                    
                    // Finaliza a linha com a célula de ações
                    newRow += `
                            <td>
                                <button type="button" class="btn btn-danger delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                            </td>
                        </tr>`;
                    
                    // Adiciona a linha à tabela
                    $premiTable.find('tbody').append(newRow);
                });
                
                // Inicializa a visualização de imagem para todas as linhas
                $premiTable.find('tbody tr').each(function() {
                    initPremioImagePreview($(this));
                });
                
                // Inicializa os botões de exclusão
                initDeletePremioButtons();
        } else {
            console.log("[IMAGEM-FIX] Atualizando tabela de prêmios existente preservando imagens");
            
            // Preservar o estado das imagens antes de fazer as alterações
            const imagensExistentes = [];
            
            $premiTable.find('tbody tr').each(function() {
                const $row = $(this);
                const rowIndex = $row.index();
                const $imgCell = $row.find('td:eq(1)');
                const $imgPreview = $imgCell.find('.premio-image-preview');
                
                // Salva informações sobre a imagem
                let imagemInfo = {
                    index: rowIndex,
                    temImagem: $imgPreview.find('img').length > 0,
                    temBotaoRemover: $imgPreview.find('.remove-premio-image').length > 0,
                    url: $imgPreview.find('img').attr('src') || null
                };
                
                imagensExistentes.push(imagemInfo);
                console.log(`[IMAGEM-FIX] Salvando estado da imagem para linha ${rowIndex}: ${JSON.stringify(imagemInfo)}`);
            });
            
            // Para cada linha existente, ajustar apenas as células de valor dos níveis
            $premiTable.find('tbody tr').each(function() {
                const $row = $(this);
                const rowIndex = $row.index();
                
                // Remove as células de nível existentes (mantém a primeira, segunda e última)
                $row.find('td').each(function(index) {
                    if (index !== 0 && index !== 1 && index !== $row.find('td').length - 1) {
                        $(this).remove();
                    }
                });
                
                // Adiciona novas células para cada nível
                let cellsHtml = '';
                niveis.forEach(nivel => {
                    cellsHtml += `
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                        </td>`;
                });
                
                // Insere as novas células antes da última
                $(cellsHtml).insertBefore($row.find('td:last'));
                
                // Restaura o estado da imagem baseado nos dados salvos
                const imagemInfo = imagensExistentes.find(img => img.index === rowIndex);
                
                if (imagemInfo && imagemInfo.temImagem) {
                    const $imgCell = $row.find('td:eq(1)');
                    const $imgContainer = $imgCell.find('.premio-image-container');
                    const $imgPreview = $imgContainer.find('.premio-image-preview');
                    const fileInput = $imgContainer.find('.premio-image');
                    
                    // Se tem imagem mas não tem botão de remover, restaura com o botão
                    if (!imagemInfo.temBotaoRemover) {
                        console.log(`[IMAGEM-FIX] Restaurando botão de remoção para imagem na linha ${rowIndex}`);
                        
                        // Recria a preview com botão de remoção
                        $imgPreview.html(`
                            <div style="position: relative; width: 100%; height: 100%;">
                                <img src="${imagemInfo.url}" style="max-width: 100%; max-height: 32px; position: relative;">
                                <div class="remove-premio-image" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                    <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                                </div>
                            </div>
                        `);
                        
                        // Redefine eventos para o botão de remoção
                        $imgPreview.find('.remove-premio-image').off('click').on('click', function(e) {
                            console.log('[DEBUG-PREMIO] Removendo imagem do prêmio');
                            e.stopPropagation();
                            $imgPreview.html('<i class="fa fa-plus"></i>');
                            fileInput.val('');
                        });
                    }
                }
            });
        }
        
        console.log("[IMAGEM-FIX] Atualização da tabela de prêmios concluída");
    }

    function updateLevel(id, name, players, premium_players, owner_premium, imageData = null) {
        console.log(`Atualizando nível ID ${id} - Nome: ${name}`);
        
        // Backup das imagens existentes
        const imagensBackup = {};
        niveisData.forEach(nivel => {
            if (nivel.image) {
                imagensBackup[nivel.id] = nivel.image;
            }
        });
        
        // Encontra o nível nos dados em memória
        const levelIndex = niveisData.findIndex(nivel => nivel.id == id);
        if (levelIndex >= 0) {
            // Preserva os dados atuais para comparação
            const nivelAntigo = {...niveisData[levelIndex]};
            console.log("Dados anteriores:", nivelAntigo);
            console.log("Imagem anterior:", nivelAntigo.image ? "Sim" : "Não");
            console.log("Nova imagem:", imageData ? "Sim" : "Não");
            
            // Determina qual imagem usar
            let imagemFinal = imageData;
            
            // Se não foi fornecida uma nova imagem (null/undefined) E não houve remoção explícita,
            // mantém a imagem existente
            if ((imageData === null || imageData === undefined) && !imageWasRemoved && nivelAntigo.image) {
                console.log("Mantendo imagem existente");
                imagemFinal = nivelAntigo.image;
            } else if (imageWasRemoved) {
                console.log("Imagem foi removida explicitamente");
                imagemFinal = null;
            }
            
            // Atualiza os dados em memória preservando a ordem e outras propriedades
            niveisData[levelIndex] = {
                ...nivelAntigo,
                name: name,
                players: parseInt(players) || 0,
                premium_players: parseInt(premium_players) || 0,
                owner_premium: !!owner_premium,
                image: imagemFinal
            };
            
            // Restaura as imagens do backup para os outros níveis
            niveisData.forEach(nivel => {
                if (nivel.id !== id && imagensBackup[nivel.id]) {
                    nivel.image = imagensBackup[nivel.id];
                }
            });
            
            // Atualiza o localStorage com as imagens atuais
            try {
                const imagensParaArmazenar = {...imagensBackup};
                if (imagemFinal) {
                    imagensParaArmazenar[id] = imagemFinal;
                } else {
                    delete imagensParaArmazenar[id];
                }
                localStorage.setItem('niveisImagens', JSON.stringify(imagensParaArmazenar));
                console.log(`${Object.keys(imagensParaArmazenar).length} imagens salvas no localStorage`);
            } catch (e) {
                console.error("Erro ao salvar imagens no localStorage:", e);
            }
            
            // Renderiza toda a tabela novamente
            renderNiveisTable();
            
            // Atualiza a tabela de prêmios sem resetar as linhas
            updatePremiosTableWithoutReset();
            
            // Reinicializa o drag and drop
            initDragAndDrop();
            
            // Limpa o campo de imagem e o preview
            $("#image").val('');
            $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
            
            // Reset imageWasRemoved flag
            imageWasRemoved = false;
        } else {
            console.error("Nível não encontrado para atualizar:", id);
            toastr.error("Erro ao atualizar nível. O nível não foi encontrado.");
        }
    }

    function resetForm() {
        $("#form-futliga")[0].reset();
        
        // Reinicializa completamente o previsualizador e input de imagem
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        
        // Limpa o valor do input de arquivo
        $("#image").val('');
        
        $('.i-checks').iCheck('update');
        
        if (isEditing) {
            $("#submit-btn").html('<i class="fa fa-plus mr5"></i> Adicionar');
            isEditing = false;
            editingId = null;
        }
        
        // Resetar o flag de remoção de imagem
        imageWasRemoved = false;
        
        // Revincula eventos no input de imagem
        $("#image").off().on('change', function() {
            const file = this.files[0];
            if (file) {
                // Validações
                if (!file.type.match('image.*')) {
                    toastr.error('Por favor, selecione uma imagem válida');
                    this.value = '';
                    return;
                }

                if (file.size > 2 * 1024 * 1024) {
                    toastr.error('A imagem não pode ter mais que 2MB');
                    this.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function(e) {
                    $("#image-preview").html(`
                        <img src="${e.target.result}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                        <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                            <i class="fa fa-trash"></i>
                        </button>
                    `);
                    $('#image-preview').css('margin-top', '-7px');
                    
                    // Adiciona handler para o botão de remover
                    $('#remove_image_btn').on('click', function() {
                        $('#image').val('');
                        $('#image-preview').html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
                        return false;
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }

    function checkDuplicateName(name) {
        let isDuplicate = false;
        $("#table tbody tr").each(function() {
            const rowName = $(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
            if (rowName.toLowerCase() === name.toLowerCase()) {
                isDuplicate = true;
                return false;
            }
        });
        return isDuplicate;
    }

    function saveOrder() {
        console.log('[ORDEM] Salvando nova ordem dos níveis');
        
        // Coleta os IDs dos níveis na ordem atual
        const niveisOrdem = [];
        $("#table tbody tr").each(function(index) {
            const id = $(this).data('id');
            $(this).attr('data-order', index + 1);
            niveisOrdem.push({
                id: id,
                ordem: index + 1
            });
        });
        
        console.log('[ORDEM] Nova ordem dos níveis:', niveisOrdem);
        
        // Salva a ordem no servidor
        $.ajax({
            url: '/futligas/niveis/ordem/',
            type: 'POST',
            data: JSON.stringify({ niveis: niveisOrdem }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                console.log('[ORDEM] Ordem salva com sucesso:', response);
                
                // Atualiza a tabela de prêmios quando a ordem dos níveis muda
                updatePremiosTable();
                
                toastr.success('Ordem dos níveis atualizada com sucesso!');
            },
            error: function(xhr, status, error) {
                console.error('[ORDEM] Erro ao salvar ordem:', error);
                console.error('[ORDEM] Resposta do servidor:', xhr.responseText);
                
                // Mesmo com erro, atualiza a tabela de prêmios para manter UI consistente
                updatePremiosTable();
                
                // Mostra mensagem de erro mas não reverte a ordem visualmente
                toastr.warning('A ordem foi alterada localmente, mas não foi salva no servidor. A ordem será resetada ao recarregar a página.');
            }
        });
    }

    function updatePremiosTable() {
        console.log('[DEPURAÇÃO] INÍCIO da função updatePremiosTable()');
        
        // Obtém a lista de níveis disponíveis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        console.log("[DEPURAÇÃO] Níveis disponíveis para a tabela de prêmios:", niveis);
        
        // Verifica se a tabela tem o seletor correto
        const $premiosTable = $('#premiosTable');
        console.log("[DEPURAÇÃO] Referência da tabela de prêmios:", $premiosTable.length > 0 ? "Encontrada" : "NÃO ENCONTRADA");
        
        // CORREÇÃO: Verificar se estamos em carregamento inicial ou atualização
        // Só criar as 3 posições iniciais durante o carregamento inicial, não em atualizações
        const isInitialLoad = !window.premiosInitialized;
        console.log("[DEPURAÇÃO] É carregamento inicial?", isInitialLoad);
        
        // Verifica quantas posições existem
        let premioRows = $premiosTable.find('tbody tr').length;
        console.log("[DEPURAÇÃO] Número de linhas de prêmios existentes:", premioRows);
        
        if (premioRows === 0 && isInitialLoad) {
            console.log("[DEPURAÇÃO] Primeira inicialização - criando linhas de prêmios padrão");
            // Adiciona pelo menos 3 posições se não houver nenhuma e for o carregamento inicial
            for (let i = 1; i <= 3; i++) {
                $premiosTable.find('tbody').append(`
                    <tr data-position="${i}" data-id="">
                        <td>${i}°</td>
                        <td class="center-middle">
                            <div class="premio-image-preview" style="display: flex; align-items: center; justify-content: center; padding: 0 10px 10px 10px; position: relative;">
                                <i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;"></i>
                                <input type="file" class="premio-image" accept="image/*" style="display: none;">
                            </div>
                        </td>
                        ${niveis.map(() => '<td class="premio-valor"><input type="text" class="form-control premio-input" placeholder="Valor"></td>').join('')}
                        <td>
                            <button type="button" class="btn btn-danger btn-sm delete-premio"><i class="glyphicon glyphicon-trash"></i></button>
                        </td>
                    </tr>
                `);
            }
            
            // Marca que já inicializamos
            window.premiosInitialized = true;
        }
        
        // Redefine o cabeçalho da tabela com base nos níveis
        const headerRow = $premiosTable.find('thead tr');
        
        // Limpa as colunas de níveis existentes
        headerRow.find('th:not(:first-child):not(:last-child):not(.center-middle)').remove();
        
        console.log("[DEPURAÇÃO] Cabeçalho da tabela de prêmios limpo e preparado para nova renderização");
        
        // Adiciona colunas para cada nível
        niveis.forEach(nivel => {
            headerRow.find('th:last-child').before(`<th class="per15">${nivel}</th>`);
        });
        
        console.log("[DEPURAÇÃO] Adicionadas", niveis.length, "colunas de níveis ao cabeçalho");
        
        // Atualiza as células de valor para cada nível
        $premiosTable.find('tbody tr').each(function() {
            const $row = $(this);
            const position = $row.attr('data-position');
            
            console.log(`[DEPURAÇÃO] Atualizando linha de prêmio posição ${position}`);
            
            // Remove todas as células de valor existentes
            $row.find('td.premio-valor').remove();
            
            // Adiciona células de valor para cada nível
            niveis.forEach(nivel => {
                $row.find('td:last-child').before(`<td class="premio-valor"><input type="text" class="form-control premio-input" placeholder="Valor"></td>`);
            });
        });
        
        // Inicializa os botões de exclusão
        initDeletePremioButtons();
        
        // Inicializa os previews de imagem
        $premiosTable.find('tbody tr').each(function() {
            initPremioImagePreview($(this));
        });
        
        console.log('[DEPURAÇÃO] FIM da função updatePremiosTable()');
    }

    // Função para atualizar a interface com dados do servidor
    function updateUIWithServerData(data) {
        console.log("Atualizando interface com dados do servidor:", data);
        
        // Limpa a tabela de níveis
        $('#table tbody').empty();
        
        // Adiciona níveis à tabela
        data.levels.forEach(nivel => {
            const newRow = $('<tr>')
                .attr('data-id', nivel.id)
                .attr('data-order', nivel.order)
                .addClass('nivel-row');

            // Adiciona células da linha
            const nomeHTML = `
                <span class="handle" style="cursor: grab;"><i class="fa fa-bars"></i></span> ${nivel.name}
            `;

            newRow.append($('<td>').html(nomeHTML));
            
            // Célula de imagem
            const colImagem = $('<td>').addClass('center-middle');
            
            if (nivel.image) {
                // Adiciona imagem existente
                colImagem.html(`
                    <div class="nivel-image-container" style="position: relative; display: inline-block;">
                        <img src="${nivel.image}" height="32" width="32" alt="Imagem" style="object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                    </div>
                `);
            } else {
                // Adiciona placeholder
                colImagem.html(
                    '<i class="fa fa-file-image-o" style="font-size: 24px; color: #ccc;"></i>'
                );
            }
            newRow.append(colImagem);
            
            // Células de jogadores e craques
            newRow.append($('<td>').text(nivel.players));
            newRow.append($('<td>').text(nivel.premium_players));
            
            // Célula de dono craque
            const donoCraque = $('<td>').addClass('center-middle');
            if (nivel.owner_premium) {
                donoCraque.html('<i class="fa fa-check text-success"></i>');
            } else {
                donoCraque.html('<i class="fa fa-times text-danger"></i>');
            }
            newRow.append(donoCraque);
            
            // Célula de ações
            const colAcoes = $('<td>').addClass('center-middle');
            colAcoes.append(
                $('<button>').attr({
                    'type': 'button',
                    'class': 'btn btn-info btn-sm mr5',
                    'title': 'Editar'
                }).html('<i class="fa fa-edit"></i>')
            );
            colAcoes.append(
                $('<button>').attr({
                    'type': 'button',
                    'class': 'btn btn-danger btn-sm',
                    'title': 'Excluir'
                }).html('<i class="fa fa-trash"></i>')
            );
            newRow.append(colAcoes);
            
            // Adiciona linha à tabela
            $('#table tbody').append(newRow);
        });
        
        // Limpa tabela de prêmios
        $('#premios table tbody').empty();
        
        // Adiciona prêmios
        if (data.prizes && data.prizes.length > 0) {
            console.log("Atualizando tabela de prêmios com", data.prizes.length, "prêmios");
            
            data.prizes.forEach(premio => {
                console.log(`Criando linha para o prêmio posição ${premio.position}, ID=${premio.id}`);
                
                const newRow = $(`
                    <tr data-position="${premio.position}" ${premio.id ? `data-id="${premio.id}"` : ''}>
                        <td>${premio.position}°</td>
                        <td class="center-middle">
                            <div class="premio-image-container" style="position: relative; display: inline-block;">
                                ${premio.image ?
                                `<img src="${premio.image}" height="32" width="32" alt="Imagem" style="object-fit: contain;">` :
                                `<i class="fa fa-plus"></i>`
                                }
                            </div>
                            <input type="file" class="premio-image" style="display: none;" accept="image/*">
                        </td>
                `);
                
                // Adiciona células para cada nível
                data.levels.forEach(nivel => {
                    const valorPremio = premio.values && premio.values[nivel.name] !== undefined ? premio.values[nivel.name] : 1000;
                    
                    newRow.append(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel.name}" value="${valorPremio}" min="0">
                        </td>
                    `);
                });
                
                // Adiciona coluna de ações
                newRow.append(`
                    <td>
                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir">
                            <i class="glyphicon glyphicon-trash"></i>
                        </button>
                    </td>
                `);
                
                $('#premios table tbody').append(newRow);
                
                // Inicializa manipuladores de eventos
                const row = $('#premios table tbody tr').last();
                initPremioImagePreview(row);
                
                console.log(`Criada linha para o prêmio posição ${premio.position}, ID=${premio.id}`);
            });
        }
        
        // Inicializa eventos para imagens de prêmios
        $('#premios table .dropzone-imagem').each(function() {
            $(this).on('click', function() {
                $(this).siblings('input[type="file"]').click();
            });
        });
    }

    // Função para lidar com o clique na dropzone
    window.handleDropzoneClick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Armazena a célula atual para uso posterior
        const currentCell = $(this).closest('td');
        
        // Cria um ID único para o input temporário
        const tempInputId = 'temp-file-input-' + Date.now();
        
        // Remove qualquer input temporário existente
        $('.temp-file-input').remove();
        
        // Cria um input de arquivo oculto
        const fileInput = $('<input type="file" class="temp-file-input" id="' + tempInputId + '" accept="image/*" style="display:none;">');
        $('body').append(fileInput);
        
        // Define um timeout para remover o input se não for usado
        setTimeout(function() {
            $('#' + tempInputId).remove();
        }, 30000);
        
        // Quando um arquivo for selecionado
        fileInput.on('change', function(e) {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const reader = new FileReader();
                
                // Mostra um indicador de carregamento
                currentCell.html('<div class="loading"><i class="fa fa-spinner fa-spin"></i></div>');
                
                reader.onload = function(e) {
                    // Cria a visualização da imagem com o botão de remover
                    const imageContainer = $(`
                        <div style="position: relative; width: 32px; height: 32px; display: inline-block;">
                            <img src="${e.target.result}" height="32" width="32" alt="Imagem" style="object-fit: contain;">
                            <div class="image-remove-btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                            </div>
                        </div>
                    `);
                    
                    // Substitui o dropzone pela imagem
                    currentCell.html(imageContainer);
                    
                    // Adiciona evento ao botão de remover
                    imageContainer.find('.image-remove-btn').on('click', function(e) {
                        e.stopPropagation();
                        
                        // Recria o dropzone
                        const dropzone = $(`
                            <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                <i class="fa fa-plus"></i>
                            </div>
                        `);
                        
                        imageContainer.replaceWith(dropzone);
                        
                        // Reaplica o evento de clique ao novo dropzone
                        dropzone.on('click', handleDropzoneClick);
                    });
                    
                    // Armazena dados da imagem para envio
                    currentCell.data('imageBase64', e.target.result);
                };
                
                reader.readAsDataURL(file);
            }
        });
        
        // Abre o seletor de arquivo
        fileInput.click();
    };
    
    // Delegação de evento para o botão de remover imagem
    $(document).on('click', '.image-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const cell = $(this).closest('td');
        cell.html(`
            <div class="dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                <i class="fa fa-plus"></i>
            </div>
        `);
        
        toastr.success('Imagem removida com sucesso!');
    });

    // Ajuste para o plugin de importação de Excel
    $('#importFile').on('change', function() {
        const file = this.files[0];
        if (file) {
            const filename = file.name;
            $(this).closest('.input-group').find('input[type="text"]').val(filename);
        }
    });

    // Função para reinicializar o estado do modal
    function resetModalState() {
        // Limpa os dados armazenados no modal
        $('#modalConfirmDelete').removeData('row');
        
        // Garante que o botão de confirmação esteja habilitado e com texto correto
        $('#confirmDeleteButton').prop('disabled', false).html('Excluir');
    }
    
    // Quando o modal é fechado, reinicia seu estado
    $('#modalConfirmDelete').on('hidden.bs.modal', function() {
        resetModalState();
        
        // Verifica se há backdrop residual e remove
        if ($('.modal-backdrop').length) {
            $('.modal-backdrop').remove();
        }
        
        // Garante que o body não tenha a classe modal-open se não houver modais abertos
        if ($('.modal.in').length === 0) {
            $('body').removeClass('modal-open');
        }
    });

    // Função para criar o html do botão de remoção de imagem
    function createImagePreviewWithRemoveButton(imageUrl) {
        return `
            <img src="${imageUrl}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
            <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
            </button>
        `;
    }

    // Função para criar o html do preview padrão sem imagem
    function createDefaultImagePreview() {
        return '<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>';
    }

    // Ajuste do problema de AJAX - garante que as URLs são corretas
    $(document).ajaxSend(function(event, jqxhr, options) {
        // Logs para debug
        console.log("URL da requisição antes:", options.url);
        
        // Remover possíveis prefixos em URLs absolutas
        if (options.url && options.url.startsWith('/administrativo')) {
            options.url = options.url.replace('/administrativo', '');
            console.log("URL corrigida:", options.url);
        }
        
        console.log("URL da requisição após ajuste:", options.url);
    });
    
    // Adiciona CSS para o cursor de arrastar e imagens
    $("<style>")
        .prop("type", "text/css")
        .html(`
            .drag-handle {
                cursor: move;
                margin-right: 8px;
                color: #999;
            }
            .tDnD_whileDrag {
                background-color: #f5f5f5 !important;
            }
            .position-relative {
                position: relative;
                display: inline-block;
            }
            .center-middle {
                text-align: center;
                vertical-align: middle !important;
            }
            .label-card {
                display: inline-block;
                padding: 10px;
                border: 2px dashed #ccc;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .label-card:hover {
                border-color: #1ab394;
            }
            .label-card-small {
                padding: 5px;
            }
            .label-content {
                font-size: 48px;
                color: #ccc;
            }
            .input-image {
                display: none;
            }
            .remove-image {
                position: absolute;
                bottom: -7px;
                right: -30px;
                padding: 2px 5px;
                font-size: 10px;
            }
            #image-preview {
                min-height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .dropzone-imagem:hover {
                background-color: #f9f9f9;
                border-color: #1ab394;
            }
        `)
        .appendTo("head");

    // Função para verificar se URLs requerem ajuste (usando jQuery)
    function isURLValid(url) {
        var result = false;
        $.ajax({
            url: url,
            type: 'HEAD',
            async: false,
            success: function() {
                result = true;
            }
        });
        return result;
    }

    // Inicializa os botões de exclusão de prêmios
    initDeletePremioButtons();

    // ... existing code ...
            // Registra estado atual das imagens de cada nível
            let niveisComImagens = 0;
            let imagensNiveis = {};
            
            $('#table tbody tr').each(function() {
                const nivelId = $(this).data('id');
                const nivelNome = $(this).find('td:eq(0)').text().trim();
                const temImagem = $(this).find('td:eq(1)').data('has-image') || $(this).find('td:eq(1) img').length > 0;
                const imagemSrc = temImagem ? $(this).find('td:eq(1) img').attr('src') : null;
                
                imagensNiveis[nivelId] = {
                    nome: nivelNome,
                    temImagem: temImagem,
                    imagemUrl: imagemSrc ? (imagemSrc.substring(0, 30) + '...') : null
                };
                
                if (temImagem) niveisComImagens++;
                
                console.log(`[DIAGNÓSTICO-IMAGEM] PRÉ-SALVAMENTO: Nível ID=${nivelId}, Nome=${nivelNome}, Tem imagem=${temImagem}`);
            });
            
    // Adiciona o modal de confirmação de exclusão
    if (!$('#confirmDeletePrizeModal').length) {
        $('body').append(`
            <div class="modal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-labelledby="confirmDeletePrizeModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-sm" role="document">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title" id="confirmDeletePrizeModalLabel">Confirmar Exclusão</h5>
                            <button type="button" class="close text-white" data-dismiss="modal" aria-label="Fechar">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            Tem certeza que deseja excluir este prêmio?
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-danger" id="confirmDeletePrize">Excluir</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    // Inicializa as visualizações de imagem para os prêmios existentes
    $('#premiosTable tbody tr').each(function() {
        initPremioImagePreview($(this));
    });
    
    // Inicializa os botões de exclusão
    initDeletePremioButtons();

    // ... existing code ...

    // Handler para o botão de adicionar prêmio
    $('.btn-adicionar-premio').off('click').on('click', function() {
        console.log('[DEBUG-PREMIO] ============ INICIANDO ADIÇÃO DE PRÊMIO ============');
        console.log('[DEBUG-PREMIO] Botão adicionar prêmio clicado');
        
        try {
            // Obtém a lista de níveis disponíveis
            const niveis = [];
            $("#table tbody tr").each(function() {
                const nivelNome = $(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
                niveis.push(nivelNome);
            });
            
            console.log('[DEBUG-PREMIO] Níveis disponíveis para o novo prêmio:', niveis);
            
            // Verifica se há níveis disponíveis
            if (niveis.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Tentativa de adicionar prêmio sem níveis definidos');
                toastr.error('Não é possível adicionar prêmios sem níveis definidos. Adicione pelo menos um nível primeiro.');
                return;
            }
            
            // Verifica se o seletor aponta para a tabela correta
            const $premiosTable = $('#premiosTable');
            if ($premiosTable.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Tabela de prêmios #premiosTable não encontrada!');
                toastr.error('Erro ao encontrar a tabela de prêmios.');
                return;
            }
            
            console.log(`[DEBUG-PREMIO] Tabela de prêmios encontrada, estrutura: cabeçalho=${$premiosTable.find('thead th').length} colunas, corpo=${$premiosTable.find('tbody tr').length} linhas`);
            
            // Valida a estrutura da tabela
            if ($premiosTable.find('thead th').length < 3) { // Pelo menos posição, imagem e uma coluna de ação
                console.error('[DEBUG-PREMIO] ERRO: Estrutura do cabeçalho da tabela inválida:', $premiosTable.find('thead th').length);
                toastr.error('Estrutura da tabela de prêmios inválida.');
                return;
            }
            
            // Calcula próxima posição
            const nextPosition = $premiosTable.find('tbody tr').length + 1;
            console.log(`[DEBUG-PREMIO] Adicionando prêmio na posição ${nextPosition}`);
            
            // Criar uma nova linha como elemento jQuery
            const $newRow = $('<tr>')
                .attr('data-position', nextPosition);
            
            // Adicionar célula de posição
            $newRow.append($('<td>').text(`${nextPosition}°`));
            
            // Adicionar célula de imagem
            const $imageCell = $('<td>').addClass('center-middle');
            const $imageContainer = $('<div>').addClass('premio-image-container').css({
                position: 'relative',
                display: 'inline-block'
            });
            
            const $imagePreview = $('<div>').addClass('premio-image-preview dropzone-imagem').css({
                height: '32px',
                width: '32px',
                border: '1px dashed #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }).append($('<i>').addClass('fa fa-plus'));
            
            const $fileInput = $('<input>').attr({
                type: 'file',
                class: 'premio-image',
                accept: 'image/*'
            }).css('display', 'none');
            
            $imageContainer.append($imagePreview).append($fileInput);
            $imageCell.append($imageContainer);
            $newRow.append($imageCell);
            
            console.log(`[DEBUG-PREMIO] Células de posição e imagem adicionadas`);
            
            // Adicionar células para cada nível
            console.log(`[DEBUG-PREMIO] Adicionando células para ${niveis.length} níveis`);
            
            niveis.forEach((nivel, idx) => {
                const $nivelCell = $('<td>');
                const $input = $('<input>').attr({
                    type: 'number',
                    class: 'form-control premio-valor',
                    'data-nivel': nivel,
                    value: '1000',
                    min: '0'
                });
                
                $nivelCell.append($input);
                $newRow.append($nivelCell);
                
                console.log(`[DEBUG-PREMIO] Adicionada célula para nível '${nivel}' na posição ${idx+1}`);
            });
            
            // Adicionar célula de ações
            const $actionsCell = $('<td>');
            const $deleteButton = $('<button>').attr({
                type: 'button',
                class: 'btn btn-danger btn-xs delete-premio',
                title: 'Excluir'
            }).append($('<i>').addClass('glyphicon glyphicon-trash'));
            
            $actionsCell.append($deleteButton);
            $newRow.append($actionsCell);
            
            console.log(`[DEBUG-PREMIO] Célula de ações adicionada`);
            console.log(`[DEBUG-PREMIO] Nova linha criada com ${$newRow.find('td').length} células`);
            
            // Validar se a linha tem o número correto de células
            const expectedCells = 2 + niveis.length + 1; // posição + imagem + níveis + ações
            if ($newRow.find('td').length !== expectedCells) {
                console.error(`[DEBUG-PREMIO] ERRO: Número incorreto de células na nova linha: ${$newRow.find('td').length}, esperado: ${expectedCells}`);
            }
            
            // Adicionar a linha à tabela
            $premiosTable.find('tbody').append($newRow);
            
            console.log(`[DEBUG-PREMIO] Linha adicionada à tabela`);
            
            // Verificar se os atributos data-nivel foram definidos corretamente
            $newRow.find('input.premio-valor').each(function(idx) {
                const $input = $(this);
                const nivel = $input.data('nivel');
                console.log(`[DEBUG-PREMIO] Input #${idx+1} - data-nivel="${nivel}"`);
                
                if (!nivel) {
                    console.error(`[DEBUG-PREMIO] ERRO: Atributo data-nivel não definido para input #${idx+1}`);
                }
            });
            
            // Inicializar manipulador para upload de imagem
            initPremioImagePreview($newRow);
            
            // Reaplica os eventos aos botões de exclusão
            initDeletePremioButtons();
            
            console.log('[DEBUG-PREMIO] Novo prêmio adicionado com sucesso');
            console.log('[DEBUG-PREMIO] ============ FIM DA ADIÇÃO DE PRÊMIO ============');
            
            toastr.success('Prêmio adicionado com sucesso!');
        } catch (error) {
            console.error('[DEBUG-PREMIO] ERRO durante a adição de prêmio:', error);
            console.error('[DEBUG-PREMIO] Stack trace:', error.stack);
            toastr.error('Erro ao adicionar prêmio. Verifique o console para mais detalhes.');
        }
    });

    // Garante que o modal de confirmação de exclusão exista no DOM
    if ($('#confirmDeletePrizeModal').length === 0) {
        console.log('[DEBUG-PREMIO] Criando modal de confirmação de exclusão');
        $('body').append(`
            <div class="modal inmodal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-hidden="true">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Fechar</span></button>
                            <h4 class="modal-title">Confirmar Exclusão</h4>
                        </div>
                        <div class="modal-body">
                            <p>Tem certeza que deseja excluir este prêmio?</p>
                            <p class="text-danger">Esta ação não poderá ser desfeita.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-white" data-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-danger" id="confirmDeletePrize">Excluir</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    // Função para coletar os prêmios da tabela HTML para o modelo de dados
    function collectPrizesFromTable() {
        console.log('[DEBUG-PREMIO] Coletando prêmios da tabela HTML');
        const prizes = [];
        
        // Obtém todos os prêmios da tabela
        $('#premiosTable tbody tr').each(function() {
            const $row = $(this);
            const position = parseInt($row.find('td:eq(0)').text().replace('°', '').trim());
            
            // CORREÇÃO: Tenta obter o ID de várias formas
            let id = $row.data('id');
            if (!id) {
                id = $row.attr('data-id');
            }
            
            // Se o ID for string vazia, define como null
            if (id === '') {
                id = null;
            } else if (id && !isNaN(parseInt(id))) {
                id = parseInt(id);
            }
            
            console.log(`[DEBUG-PREMIO] Processando prêmio posição ${position}, ID ${id}`);
            
            // Obtém a imagem
            const $img = $row.find('.premio-image-preview img');
            let image = null;
            
            if ($img.length > 0) {
                image = $img.attr('src');
                console.log(`[DEBUG-PREMIO] Prêmio posição ${position} tem imagem: ${image.substring(0, 30)}...`);
            }
            
            // Coleta os valores para cada nível
            const values = {};
            $row.find('.premio-valor').each(function() {
                const $input = $(this);
                const nivel = $input.data('nivel');
                const valor = parseInt($input.val() || 0);
                
                if (nivel) {
                    values[nivel] = valor;
                }
            });
            
            // Adiciona o prêmio ao array
            prizes.push({
                id: id,
                position: position,
                image: image,
                values: values,
                league_id: 6  // FIXME: Pegar o league_id dinamicamente
            });
            
            console.log(`[DEBUG-PREMIO] Prêmio coletado - posição: ${position}, ID: ${id}, valores: ${Object.keys(values).length}`);
        });
        
        return prizes;
    }

    // Botão de salvar
    $('#successToast').on('click', function(e) {
        e.preventDefault();
        
        const $btn = $(this);
        const originalHtml = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin"></i> Salvando...').prop('disabled', true);
        
        console.log('[DEBUG-PREMIO] ============ PREPARANDO DADOS PARA SALVAMENTO ============');
        
        // Coleta dados dos níveis
        const niveis = [];
        $('#table tbody tr').each(function() {
            const $row = $(this);
            
            // CORREÇÃO: Tenta obter o ID de várias formas
            let id = $row.data('id');
            if (!id && row.attr('data-id')) {
                id = $row.attr('data-id');
                console.log(`[DEBUG-PREMIO] ID obtido via attr data-id: ${id}`);
            }
            
            const name = $row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
            const players = parseInt($row.find('td:eq(2)').text());
            const premium_players = parseInt($row.find('td:eq(3)').text());
            const owner_premium = $row.find('td:eq(4)').text().trim() === 'Sim';
            
            // Obtém a imagem
            const $img = $row.find('.nivel-image');
            let image = null;
            
            if ($img.length > 0 && $img.attr('src')) {
                image = $img.attr('src');
            }
            
            niveis.push({
                id: id,
                name: name,
                players: players,
                premium_players: premium_players,
                owner_premium: owner_premium,
                image: image
            });
            
            console.log(`[DEBUG-PREMIO] Nível coletado - nome: ${name}, ID: ${id}`);
        });
        
        // CORREÇÃO: Usa a função separada para coletar prêmios
        const premios = collectPrizesFromTable();
        
        console.log('[DEBUG-PREMIO] Resumo dos dados coletados:');
        console.log(`- Níveis: ${niveis.length}`);
        console.log(`- Prêmios: ${premios.length}`);
        console.log(`- Prêmios para exclusão: ${deletedPrizeIds.length}`);
        
        premios.forEach(premio => {
            console.log(`[DEBUG-PREMIO] Prêmio: ID=${premio.id}, Posição=${premio.position}, ` + 
                    `position: ${premio.position}, hasImage: ${!!premio.image}, ` +
                    `valuesCount: ${Object.keys(premio.values).length}`);
        });
    });

    // ... existing code ...
                            // Botão de exclusão do prêmio
                            $(document).on('click', '.btn-delete-prize', function() {
                                var prizeId = $(this).data('prize-id');
                                var row = $(this).closest('tr');
                                var posicao = row.find('td:first').text().trim();
                                
                                console.log('[DEBUG-PREMIO] Botão de exclusão clicado para prêmio ID:', prizeId, 'posição:', posicao);
                                
                                // Verifica se o ID é válido
                                if (!prizeId || prizeId === 'undefined') {
                                    console.warn('[DEBUG-PREMIO] ID do prêmio inválido:', prizeId);
                                    
                                    // Remove da interface mas avisa sobre problema
                                    globalRemoveFromInterface(row, 'Prêmio removido apenas da interface devido a ID inválido.');
                                    return;
                                }
                                
                                // Confirma exclusão
                                $('#modalConfirmDelete').modal('show');
                                $('#itemTypeText').text('o prêmio');
                                $('#levelNameToDelete').text(`da posição ${posicao}`);
                                
                                // Quando clicar em confirmar
                                $('#confirmDeleteButton').off('click').on('click', function() {
                                    $('#modalConfirmDelete').modal('hide');
                                    
                                    // Mostra indicador de carregamento
                                    row.addClass('text-muted').css('opacity', '0.6');
                                    row.find('.btn-delete-prize').html('<i class="fa fa-spinner fa-spin"></i>');
                                    
                                    console.log('[DEBUG-PREMIO] Iniciando exclusão direta do prêmio ID:', prizeId);
                                    
                                    // Requisição AJAX para obter dados atuais
                                    $.ajax({
                                        url: '/futligas/jogadores/dados/',
                                        method: 'GET',
                                        success: function(data) {
                                            console.log('[DEBUG-PREMIO] Dados carregados:', data);
                                            
                                            // Prepara o payload excluindo o prêmio específico
                                            const payload = {
                                                levels: data.levels || [],
                                                prizes: (data.prizes || []).filter(p => p.id !== prizeId),
                                                award_config: data.award_config || {
                                                    weekly: { day: "Segunda", time: "12:00" },
                                                    season: { month: "Janeiro", day: "1", time: "12:00" }
                                                },
                                                deleted_prize_ids: [prizeId]
                                            };
                                            
                                            console.log('[DEBUG-PREMIO] Enviando payload para exclusão:', payload);
                                            
                                            // Enviar para o endpoint de salvamento
                                            $.ajax({
                                                url: '/futligas/jogadores/salvar/',
                                                method: 'POST',
                                                contentType: 'application/json',
                                                data: JSON.stringify(payload),
                                                headers: {
                                                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                                                },
                                                success: function(response) {
                                                    console.log('[DEBUG-PREMIO] Resposta da exclusão:', response);
                                                    
                                                    if (response.success) {
                                                        // Exclusão bem-sucedida
                                                        row.css('background-color', '#dff0d8').delay(300);
                                                        row.fadeOut(500, function() {
                                                            $(this).remove();
                                                            updatePrizesPositions();
                                                        });
                                                        
                                                        toastr.success('Prêmio excluído com sucesso.');
                                                    } else {
                                                        // Erro na exclusão
                                                        console.error('[DEBUG-PREMIO] Erro na exclusão:', response.message);
                                                        globalRemoveFromInterface(row, `Erro ao excluir: ${response.message || 'Erro desconhecido'}`);
                                                    }
                                                },
                                                error: function(xhr) {
                                                    console.error('[DEBUG-PREMIO] Erro na requisição AJAX:', xhr.responseText);
                                                    globalRemoveFromInterface(row, 'Erro ao comunicar com o servidor.');
                                                }
                                            });
                                        },
                                        error: function() {
                                            console.error('[DEBUG-PREMIO] Erro ao carregar dados');
                                            globalRemoveFromInterface(row, 'Não foi possível carregar dados para exclusão.');
                                        }
                                    });
                                });
                            });
// ... existing code ...

    // Adiciona um hook para automaticamente restaurar os botões após qualquer operação AJAX
    $(document).ajaxComplete(function(event, xhr, settings) {
        // Se for uma operação de salvamento
        if (settings.url && (
            settings.url.includes('/futligas/jogadores/salvar/') || 
            settings.url.includes('/futligas/jogadores/premios/')
        )) {
            console.log('[IMAGEM-FIX] Detectada operação de salvamento, verificando botões de remoção de imagem');
            
            // Verifica se estamos na aba prêmios
            if ($('#premios').is(':visible') || $('#premios').hasClass('active')) {
                setTimeout(function() {
                    $('#premiosTable tbody tr').each(function() {
                        const $row = $(this);
                        const $imgCell = $row.find('td:eq(1)');
                        const $imgContainer = $imgCell.find('.premio-image-container');
                        const $imgPreview = $imgContainer.find('.premio-image-preview');
                        
                        // Se tem imagem mas não tem botão de remoção
                        if ($imgPreview.find('img').length > 0 && $imgPreview.find('.remove-premio-image').length === 0) {
                            console.log('[IMAGEM-FIX] Restaurando botão de remoção pós-AJAX');
                            
                            const imgSrc = $imgPreview.find('img').attr('src');
                            const fileInput = $imgContainer.find('.premio-image');
                            
                            // Recria o conteúdo com o botão de remoção
                            $imgPreview.html(`
                                <div style="position: relative; width: 100%; height: 100%;">
                                    <img src="${imgSrc}" style="max-width: 100%; max-height: 32px; position: relative;">
                                    <div class="remove-premio-image" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                        <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                                    </div>
                                </div>
                            `);
                            
                            // Redefine eventos para o botão de remoção
                            $imgPreview.find('.remove-premio-image').off('click').on('click', function(e) {
                                console.log('[DEBUG-PREMIO] Removendo imagem do prêmio');
                                e.stopPropagation();
                                $imgPreview.html('<i class="fa fa-plus"></i>');
                                fileInput.val('');
                            });
                        }
                    });
                }, 500); // Pequeno atraso para garantir que a tabela foi atualizada
            }
        }
    });
    // ... existing code ...

    // Adiciona uma função global para garantir que todas as imagens de prêmios tenham botões de remoção
    function garantirBotoesRemocaoImagem() {
        console.log("[FIX-BOTÕES] Verificando e restaurando botões de remoção de imagem");
        
        $('#premiosTable tbody tr').each(function() {
            const $row = $(this);
            const $imgCell = $row.find('td:eq(1)');
            const $imgContainer = $imgCell.find('.premio-image-container');
            const $imgPreview = $imgContainer.find('.premio-image-preview');
            
            // Se existe uma imagem mas não tem botão de remoção
            if ($imgPreview.find('img').length > 0 && $imgPreview.find('.remove-premio-image').length === 0) {
                const imgSrc = $imgPreview.find('img').attr('src');
                const fileInput = $imgContainer.find('.premio-image');
                
                console.log("[FIX-BOTÕES] Restaurando botão de remoção para imagem", imgSrc);
                
                // Recria o HTML com o botão de remoção
                $imgPreview.html(`
                    <div style="position: relative; width: 100%; height: 100%;">
                        <img src="${imgSrc}" style="max-width: 100%; max-height: 32px; position: relative;">
                        <div class="remove-premio-image" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
                        </div>
                    </div>
                `);
                
                // Redefine eventos para o botão de remoção
                $imgPreview.find('.remove-premio-image').off('click').on('click', function(e) {
                    console.log('[DEBUG-PREMIO] Removendo imagem do prêmio');
                    e.stopPropagation();
                    $imgPreview.html('<i class="fa fa-plus"></i>');
                    fileInput.val('');
                });
            }
        });
    }
});