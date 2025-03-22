// DefiniÃ§Ã£o da URL base para requisiÃ§Ãµes AJAX
const ADMIN_URL_PREFIX = '';

$(document).ready(function() {
    let isEditing = false;
    let editingId = null;
    let niveisData = [];
    let imageWasRemoved = false;
    
    // VariÃ¡vel global para rastrear IDs de prÃªmios excluÃ­dos
    let deletedPrizeIds = [];
    
    // Atualiza o nome do arquivo selecionado
    $('input[type="file"]').change(function(e) {
        if (e.target.files && e.target.files[0]) {
            var fileName = e.target.files[0].name;
            $(this).closest('.input-group').find('input[type="text"]').val(fileName);
        }
    });
    
    // FunÃ§Ã£o para reinicializar o drag and drop
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

    // FunÃ§Ã£o para carregar dados iniciais
    function carregarDadosIniciais() {
        // Adiciona um indicador de carregamento na tabela
        $('#table tbody').html('<tr><td colspan="6" class="text-center"><i class="fa fa-spinner fa-spin"></i> Carregando dados...</td></tr>');
        
        // Cria uma cÃ³pia de backup dos nÃ­veis atuais (se existirem)
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
        
        // Faz a requisiÃ§Ã£o AJAX para carregar os dados
        $.ajax({
            url: '/futligas/jogadores/dados/',
            method: 'GET',
            success: function(response) {
                console.log("Dados carregados com sucesso:", response);
                if (response && response.levels) {
                    // Se jÃ¡ temos dados, vamos mesclar preservando as imagens
                    if (niveisDataBackup.length > 0) {
                        console.log("Mesclando dados existentes com dados do servidor");
                        
                        // Para cada nÃ­vel carregado do servidor
                        response.levels.forEach(novoNivel => {
                            // Verifica se jÃ¡ existe um nÃ­vel com o mesmo ID
                            const nivelExistente = niveisDataBackup.find(n => n.id === novoNivel.id);
                            if (nivelExistente) {
                                console.log(`NÃ­vel ID ${novoNivel.id} jÃ¡ existe, verificando imagem`);
                                
                                // Se o nÃ­vel do servidor nÃ£o tiver imagem mas o nÃ­vel existente tiver,
                                // mantÃ©m a imagem do nÃ­vel existente
                                if (!novoNivel.image && nivelExistente.image) {
                                    console.log(`Mantendo imagem existente para nÃ­vel ID ${novoNivel.id}`);
                                    novoNivel.image = nivelExistente.image;
                                }
                            } else {
                                console.log(`Novo nÃ­vel ID ${novoNivel.id} adicionado dos dados do servidor`);
                            }
                            
                            // Verifica se temos esta imagem no localStorage
                            if (!novoNivel.image && imagensLocais[novoNivel.id]) {
                                console.log(`Recuperando imagem do localStorage para nÃ­vel ID ${novoNivel.id}`);
                                novoNivel.image = imagensLocais[novoNivel.id];
                            }
                        });
                    } else if (Object.keys(imagensLocais).length > 0) {
                        // Se nÃ£o temos dados em memÃ³ria mas temos no localStorage
                        response.levels.forEach(nivel => {
                            if (!nivel.image && imagensLocais[nivel.id]) {
                                console.log(`Recuperando imagem do localStorage para nÃ­vel ID ${nivel.id}`);
                                nivel.image = imagensLocais[nivel.id];
                            }
                        });
                    }
                    
                    // Atualiza os dados armazenados
                    niveisData = response.levels;
                    
                    // Garante que nÃ£o haja valores undefined nas imagens
                    niveisData.forEach(nivel => {
                        if (nivel.image === undefined) {
                            nivel.image = null;
                        }
                        console.log(`NÃ­vel carregado: ${nivel.name}, ID: ${nivel.id}, Imagem: ${nivel.image || 'Nenhuma'}`);
                    });
                    
                    // Preenche a tabela de nÃ­veis
                    renderNiveisTable();
                    
                    // Preenche a tabela de prÃªmios
                    updatePremiosTableWithoutReset();
                    
                    // Configura formulÃ¡rio de premiaÃ§Ã£o
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
                    
                    // Se nÃ£o hÃ¡ prÃªmios no banco de dados, deixa a tabela vazia
                    if (!response.prizes || response.prizes.length === 0) {
                        $('#premios table tbody').empty();
                        console.log("Sem prÃªmios do servidor - tabela de prÃªmios serÃ¡ inicializada vazia");
                        
                        // CORREÃ‡ÃƒO: Verifica se temos backup dos prÃªmios no localStorage
                        try {
                            const premiosBackupStr = localStorage.getItem('premiosBackup');
                            if (premiosBackupStr) {
                                const premiosBackup = JSON.parse(premiosBackupStr);
                                console.log(`[DIAGNÃ“STICO-PRÃŠMIO] Encontrado backup de ${premiosBackup.length} prÃªmios no localStorage`);
                                
                                if (premiosBackup.length > 0) {
                                    console.log("[DIAGNÃ“STICO-PRÃŠMIO] Restaurando prÃªmios do backup local");
                                    
                                    // Limpa a tabela para carregar os prÃªmios do backup
                                    $('#premios table tbody').empty();
                                    
                                    // Recupera os prÃªmios a partir do backup
                                    premiosBackup.forEach(prize => {
                                        const position = prize.position;
                                        const image = prize.image;
                                        
                                        let newRow = `
                                            <tr ${prize.id ? `data-id="${prize.id}"` : ''}>
                                                <td>${position}Â°</td>
                                                <td class="center-middle">
                                                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                                                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                                            ${image ? `<img src="${image}" style="max-width: 100%; max-height: 32px;">` : '<i class="fa fa-plus"></i>'}
                                                        </div>
                                                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                                                    </div>
                                                </td>`;
                                                
                                            // Adiciona cÃ©lulas para cada nÃ­vel
                                            niveis.forEach(nivel => {
                                                newRow += `
                                                    <td>
                                                        <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                                                    </td>`;
                                            });
                                            
                                            // Adiciona botÃ£o de exclusÃ£o
                                            newRow += `
                                                    <td>
                                                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                                                    </td>
                                                </tr>`;
                                            
                                            $('#premios table tbody').append(newRow);
                                        });
                                        
                                        // Inicializa eventos para as linhas de prÃªmios
                                        $('#premios table tbody tr').each(function() {
                                            initPremioImagePreview($(this));
                                        });
                                        
                                        initDeletePremioButtons();
                                        window.premiosInitialized = true; // Marca que jÃ¡ temos prÃªmios inicializados
                                        
                                        console.log("[DIAGNÃ“STICO-PRÃŠMIO] PrÃªmios restaurados do backup com sucesso");
                                        return; // Sair da funÃ§Ã£o para nÃ£o recriar prÃªmios padrÃ£o
                                    }
                                }
                            } catch (e) {
                                console.error("[DIAGNÃ“STICO-PRÃŠMIO] Erro ao recuperar prÃªmios do backup:", e);
                            }
                    } else {
                        console.log("Carregando prÃªmios do servidor:", response.prizes.length);
                        
                        // Limpa a tabela para carregar os prÃªmios do servidor
                        $('#premios table tbody').empty();
                        
                        // Carrega os prÃªmios do servidor na tabela
                        response.prizes.forEach(prize => {
                            const position = prize.position;
                            const image = prize.image;
                            
                            let newRow = `
                                <tr data-id="${prize.id}">
                                    <td>${position}Â°</td>
                                    <td class="center-middle">
                                        <div class="premio-image-container" style="position: relative; display: inline-block;">
                                            <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                                ${image ? `<img src="${image}" style="max-width: 100%; max-height: 32px;">` : '<i class="fa fa-plus"></i>'}
                                            </div>
                                            <input type="file" class="premio-image" style="display: none;" accept="image/*">
                                        </div>
                                    </td>`;
                                    
                            // Adiciona cÃ©lulas para cada nÃ­vel com valores do servidor
                            Object.keys(prize.values || {}).forEach(nivel => {
                                const value = prize.values[nivel];
                                newRow += `
                                    <td>
                                        <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="${value}" min="0">
                                    </td>`;
                            });
                            
                            // Adiciona botÃ£o de exclusÃ£o
                            newRow += `
                                    <td>
                                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                                    </td>
                                </tr>`;
                            
                            $('#premios table tbody').append(newRow);
                        });
                        
                        // Inicializa eventos para as linhas de prÃªmios
                        $('#premios table tbody tr').each(function() {
                            initPremioImagePreview($(this));
                        });
                        
                        initDeletePremioButtons();
                        window.premiosInitialized = true; // Marca que jÃ¡ temos prÃªmios inicializados
                    }
                } else {
                    $('#table tbody').html('<tr><td colspan="6" class="text-center">Nenhum nÃ­vel encontrado.</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                console.error("Erro ao carregar dados:", error);
                console.error("Status HTTP:", xhr.status);
                console.error("Resposta:", xhr.responseText);
                
                $('#table tbody').html('<tr><td colspan="6" class="text-center text-danger">Erro ao carregar dados. <button class="btn btn-xs btn-primary" id="btn-retry">Tentar novamente</button></td></tr>');
                
                // Adiciona listener para o botÃ£o de tentar novamente
                $('#btn-retry').on('click', function() {
                    carregarDadosIniciais();
                });
                
                toastr.error('Ocorreu um erro ao carregar os dados. Por favor, verifique o console para mais detalhes ou tente novamente.');
            }
        });
    }
    
    // Renderiza a tabela de nÃ­veis de forma robusta
    function renderNiveisTable() {
        console.log("Renderizando tabela de nÃ­veis com", niveisData ? niveisData.length : 0, "nÃ­veis");
        
        // CORREÃ‡ÃƒO: Recuperar imagens do localStorage antes de renderizar
        try {
            const imagensLocaisStr = localStorage.getItem('niveisImagens');
            if (imagensLocaisStr) {
                const imagensLocais = JSON.parse(imagensLocaisStr);
                console.log("Imagens recuperadas do localStorage:", Object.keys(imagensLocais).length);
                
                // Aplica imagens do localStorage para nÃ­veis sem imagem
                niveisData.forEach(nivel => {
                    if (!nivel.image) {
                        // Tenta recuperar por ID
                        if (nivel.id && imagensLocais[nivel.id]) {
                            console.log(`Recuperando imagem do localStorage por ID para nÃ­vel ID ${nivel.id}`);
                            nivel.image = imagensLocais[nivel.id];
                        }
                        // Tenta por nome+ordem
                        else {
                            const chaveAlternativa = `${nivel.name}_${nivel.order}`;
                            if (imagensLocais[chaveAlternativa]) {
                                console.log(`Recuperando imagem do localStorage via chave alternativa para nÃ­vel ${nivel.name}`);
                                nivel.image = imagensLocais[chaveAlternativa];
                            }
                            // Tenta por nome
                            else if (imagensLocais[`nome_${nivel.name}`]) {
                                console.log(`Recuperando imagem do localStorage via nome para nÃ­vel ${nivel.name}`);
                                nivel.image = imagensLocais[`nome_${nivel.name}`];
                            }
                        }
                    }
                });
            }
        } catch (e) {
            console.error("Erro ao recuperar imagens do localStorage:", e);
        }
        
        // Guarda as imagens atuais na tabela para referÃªncia
        const imagensAtuais = {};
        $('#table tbody tr').each(function() {
            const id = $(this).data('id');
            const imgElement = $(this).find('td:eq(1) img');
            if (imgElement.length && imgElement.attr('src')) {
                imagensAtuais[id] = imgElement.attr('src');
                console.log(`Imagem encontrada na tabela para nÃ­vel ID ${id}: ${imgElement.attr('src')}`);
            }
        });
        
        if (!niveisData || niveisData.length === 0) {
            $('#table tbody').html('<tr><td colspan="6" class="text-center">Nenhum nÃ­vel encontrado.</td></tr>');
            return;
        }
        
        // Validar os dados das imagens antes de renderizar
        niveisData.forEach(nivel => {
            // Verificar se temos uma imagem na tabela atual que nÃ£o estÃ¡ nos dados
            if (!nivel.image && imagensAtuais[nivel.id]) {
                console.log(`Recuperando imagem da tabela para nÃ­vel ID ${nivel.id}`);
                nivel.image = imagensAtuais[nivel.id];
            }
            
            // Garantir que a propriedade image nÃ£o se torne undefined
            if (nivel.image === undefined) {
                nivel.image = null;
            }
            
            console.log(`Renderizando nÃ­vel: ${nivel.name}, ID: ${nivel.id}, tem imagem: ${nivel.image ? 'Sim' : 'NÃ£o'}`);
        });
        
        // CORREÃ‡ÃƒO: Criar cÃ³pia profunda dos dados para evitar perdas por referÃªncia
        const niveisDataCopy = JSON.parse(JSON.stringify(niveisData.map(nivel => {
            // Preserva somente o URL da imagem na cÃ³pia, nÃ£o a imagem em si
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
                    // TambÃ©m salva com chave alternativa nome_ordem
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
            // Garante que a imagem seja exibida se estiver disponÃ­vel
            const imagemHTML = nivel.image 
                ? `<img src="${nivel.image}" height="32" width="32" alt="Imagem" onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjZWVlIi8+PHRleHQgdGV4dC1hbmNob3I9Im1pZGRsZSIgeD0iMTYiIHk9IjE2IiBzdHlsZT0iZmlsbDojYWFhO2ZvbnQtd2VpZ2h0OmJvbGQ7Zm9udC1zaXplOjEycHg7Zm9udC1mYW1pbHk6QXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWY7ZG9taW5hbnQtYmFzZWxpbmU6Y2VudHJhbCI+Pzw8L3RleHQ+PC9zdmc+'; console.log('Erro ao carregar imagem para nÃ­vel ID ' + nivel.id);">`
                : '-';
            
            html += `
            <tr data-id="${nivel.id}" data-order="${nivel.order}">
                <td><span class="drag-handle" style="cursor: move; margin-right: 5px;">&#9776;</span> ${nivel.name || '-'}</td>
                <td class="center-middle" data-has-image="${!!nivel.image}">${imagemHTML}</td>
                <td>${nivel.players || 0}</td>
                <td>${nivel.premium_players || 0}</td>
                <td>${nivel.owner_premium ? 'Sim' : 'NÃ£o'}</td>
                <td>
                    <div>
                        <button type="button" class="btn btn-info btn-xs mr5" title="Editar"><i class="glyphicon glyphicon-pencil"></i></button>
                        <button type="button" class="btn btn-danger btn-xs mr5" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                    </div>
                </td>
            </tr>`;
        });
        
        $('#table tbody').html(html);
        
        // CORREÃ‡ÃƒO: Verificar se hÃ¡ inconsistÃªncias entre os nÃ­veis renderizados e a cÃ³pia de backup
        setTimeout(function() {
            let problemas = 0;
            
            niveisDataCopy.forEach(nivelOriginal => {
                const nivelAtual = niveisData.find(n => n.id == nivelOriginal.id);
                
                if (nivelAtual) {
                    // Compara imagens
                    if (nivelOriginal.image && !nivelAtual.image) {
                        console.error(`INCONSISTÃŠNCIA: NÃ­vel ID ${nivelOriginal.id} perdeu sua imagem durante a renderizaÃ§Ã£o`);
                        // Restaura a imagem do backup
                        nivelAtual.image = nivelOriginal.image;
                        problemas++;
                    }
                } else {
                    console.error(`INCONSISTÃŠNCIA: NÃ­vel ID ${nivelOriginal.id} nÃ£o encontrado apÃ³s renderizaÃ§Ã£o`);
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
                    console.error("Erro ao atualizar imagens no localStorage apÃ³s correÃ§Ãµes:", e);
                }
            }
            
            // Verifica depois da renderizaÃ§Ã£o se as imagens estÃ£o sendo exibidas corretamente
            $('#table tbody tr').each(function() {
                const id = $(this).data('id');
                const nivel = niveisData.find(n => n.id == id);
                
                if (nivel && nivel.image) {
                    const imgElement = $(this).find('td:eq(1) img');
                    if (imgElement.length === 0) {
                        console.error(`Imagem nÃ£o renderizada para nÃ­vel ID ${id}, apesar de ter dados de imagem`);
                        
                        // CORREÃ‡ÃƒO: Tenta corrigir renderizaÃ§Ã£o da imagem
                        const imagemHTML = `<img src="${nivel.image}" height="32" width="32" alt="Imagem">`;
                        $(this).find('td:eq(1)').html(imagemHTML).attr('data-has-image', 'true');
                    }
                }
            });
        }, 500);
    }
    
    // Carrega os dados iniciais quando a pÃ¡gina carrega
    carregarDadosIniciais();

    // Preview da imagem com validaÃ§Ãµes
    $("#image").change(function() {
        const file = this.files[0];
        if (file) {
            // ValidaÃ§Ãµes
            if (!file.type.match('image.*')) {
                toastr.error('Por favor, selecione uma imagem vÃ¡lida');
                this.value = '';
                return;
            }

            if (file.size > 2 * 1024 * 1024) {
                toastr.error('A imagem nÃ£o pode ter mais que 2MB');
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
                
                // Adiciona handler para o botÃ£o de remover
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
        
        console.log("BotÃ£o de remover imagem clicado - removendo imagem intencionalmente");
        
        // Marca que a imagem foi intencionalmente removida
        imageWasRemoved = true;
        
        // Limpa o campo de arquivo
        $("#image").val('');
        
        // Reinicia o visualizador
        $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        
        // Garante que o evento nÃ£o propague para outros elementos
        return false;
    });

    // Submit do formulÃ¡rio
    $("#form-futliga").submit(function(e) {
        e.preventDefault();
        
        console.log('==== ENVIANDO FORMULÃRIO ====');
        
        const name = $("#name").val();
        const players = $("#players").val();
        const premium_players = $("#premium_players").val();
        const owner_premium = $("#owner_premium").prop('checked');
        
        // ValidaÃ§Ãµes bÃ¡sicas
        if (!name || !players || !premium_players) {
            toastr.error('Preencha todos os campos obrigatÃ³rios!');
            return;
        }
        
        // ValidaÃ§Ã£o de nome duplicado
        if (!isEditing && checkDuplicateName(name)) {
            toastr.error('JÃ¡ existe um nÃ­vel com este nome!');
            return;
        }

        // Processar a imagem se houver
        let imageData = null;
        const imagePreview = $("#image-preview img");
        if (imagePreview.length) {
            imageData = imagePreview.attr('src');
            console.log('Imagem encontrada no formulÃ¡rio e serÃ¡ usada');
        } else {
            console.log('Nenhuma imagem encontrada no formulÃ¡rio');
            
            // Se estiver editando e a imagem NÃƒO foi removida intencionalmente, 
            // verificar se o nÃ­vel jÃ¡ tem uma imagem que deve ser mantida
            if (isEditing && !imageWasRemoved) {
                const existingLevel = niveisData.find(nivel => nivel.id == editingId);
                if (existingLevel && existingLevel.image) {
                    console.log('Mantendo imagem existente do nÃ­vel em ediÃ§Ã£o');
                    imageData = existingLevel.image;
                }
            } else if (imageWasRemoved) {
                console.log('Imagem foi intencionalmente removida pelo usuÃ¡rio');
            }
        }
        
        // Coleta posiÃ§Ãµes de prÃªmios a serem excluÃ­dos
        const deletePositions = [];
        $('input[name="delete_prize_position"]').each(function() {
            deletePositions.push(parseInt($(this).val()));
        });
        console.log("PosiÃ§Ãµes de prÃªmios para excluir:", deletePositions);
        
        // Coleta os prÃªmios visÃ­veis (nÃ£o marcados para exclusÃ£o)
        const premios = [];
        $('#premios table tbody tr:visible').each(function(index) {
            const $row = $(this);
            const position = index + 1;
            const rowId = $row.data('id');
            
            console.log(`Processando prÃªmio posiÃ§Ã£o ${position}, ID:`, rowId);
            
            // Valores por nÃ­vel
            const valores = {};
            $row.find('.premio-valor').each(function() {
                const nivel = $(this).data('nivel');
                const valor = $(this).val();
                valores[nivel] = parseInt(valor);
            });
            
            // Imagem
            const $img = $row.find('img');
            const imgSrc = $img.length ? $img.attr('src') : null;
            
            // Adiciona o prÃªmio Ã  lista
            premios.push({
                position: position,
                id: rowId === undefined ? null : rowId, // Corrige para garantir que undefined seja convertido para null
                image: imgSrc,
                values: valores
            });
        });
        
        // Adiciona os dados ao formulÃ¡rio
        const formData = {
            name: name,
            players: players,
            premium_players: premium_players,
            owner_premium: owner_premium,
            prizes: premios,
            deleted_prize_ids: deletedPrizeIds // Adiciona IDs de prÃªmios excluÃ­dos
        };
        
        console.log("Dados do formulÃ¡rio:", formData);
        console.log("IDs de prÃªmios excluÃ­dos:", deletedPrizeIds);
        
        // Atualiza ou cria o nÃ­vel
        $.ajax({
            url: "/futligas/nivel/" + (isEditing ? editingId + "/update/" : "novo/"),
            type: "POST",
            data: JSON.stringify(formData),
            contentType: "application/json",
            dataType: "json",
            success: function(response) {
                console.log("Resposta do servidor:", response);
                if (response.status === "success") {
                    toastr.success("NÃ­vel " + (isEditing ? "atualizado" : "criado") + " com sucesso!");
                    
                    // Limpa a lista de prÃªmios excluÃ­dos apÃ³s salvar com sucesso
                    deletedPrizeIds = [];
                    
                    // Recarrega a pÃ¡gina ou atualiza a interface
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    toastr.error("Erro ao " + (isEditing ? "atualizar" : "criar") + " nÃ­vel: " + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error("Erro na requisiÃ§Ã£o AJAX:", xhr.responseText);
                toastr.error("Erro ao " + (isEditing ? "atualizar" : "criar") + " nÃ­vel: " + error);
            }
        });
    });

    // Editar nÃ­vel
    $(document).on('click', '.btn-info', function() {
        const row = $(this).closest('tr');
        editingId = row.data('id');
        
        console.log(`Editando nÃ­vel ID: ${editingId}`);
        
        // ObtÃ©m o nÃ­vel dos dados em memÃ³ria para garantir todos os detalhes
        const nivel = niveisData.find(n => n.id == editingId);
        if (!nivel) {
            console.error(`NÃ­vel com ID ${editingId} nÃ£o encontrado nos dados em memÃ³ria`);
            toastr.error('Erro ao editar: nÃ­vel nÃ£o encontrado');
            return;
        }
        
        // Preenche o formulÃ¡rio com dados do nÃ­vel
        $("#name").val(nivel.name);
        $("#players").val(nivel.players);
        $("#premium_players").val(nivel.premium_players);
        $("#owner_premium").prop('checked', nivel.owner_premium).iCheck('update');
        
        // Recupera a imagem existente se houver
        if (nivel.image) {
            console.log(`NÃ­vel tem imagem: ${nivel.image}`);
            $("#image-preview").html(`
                <img src="${nivel.image}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
                <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: -7px; right: -30px;">
                    <i class="fa fa-trash"></i>
                </button>
            `);
            $('#image-preview').css('margin-top', '-7px');
        } else {
            console.log(`NÃ­vel nÃ£o tem imagem`);
            $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
        }
        
        $("#submit-btn").html('<i class="fa fa-save mr5"></i> Salvar AlteraÃ§Ãµes');
        isEditing = true;
        
        // Manter foco no formulÃ¡rio
        $('html, body').animate({
            scrollTop: $("#form-futliga").offset().top - 100
        }, 300);
    });

    // Excluir nÃ­vel - seletor especÃ­fico para botÃµes dentro da tabela de nÃ­veis
    $(document).on('click', '#table tbody tr .btn-danger:not(.img-remove-btn)', function(e) {
        console.log("BotÃ£o de exclusÃ£o de nÃ­vel clicado");
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const nivelId = row.data('id');
        const nivelNome = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
        
        // Abre o modal de confirmaÃ§Ã£o
        $('#levelNameToDelete').text(nivelNome);
        $('#modalConfirmDelete').data('row', row).modal('show');
    });

    // Adiciona evento para os botÃµes de exclusÃ£o na aba prÃªmios - versÃ£o simplificada
    $(document).on('click', '#premios table tbody tr .btn-danger', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const row = $(this).closest('tr');
        const position = row.find('td:first').text();
        
        console.log('Excluindo prÃªmio na posiÃ§Ã£o:', position);
        console.log('ID do elemento HTML:', row.attr('id'));
        console.log('Data attributes:', row.data());
        
        if (confirm('Tem certeza que deseja excluir este prÃªmio?')) {
            // Marca a linha como excluÃ­da com CSS
            row.css('background-color', '#ffcccc');
            row.css('text-decoration', 'line-through');
            
            // Adiciona um campo oculto no formulÃ¡rio para excluir este prÃªmio
            const position_str = position.replace('Â°', '');
            $('form').append(`<input type="hidden" name="delete_prize_position" value="${position_str}">`);
            
            // Mostra uma mensagem de confirmaÃ§Ã£o
            toastr.success(`PrÃªmio na posiÃ§Ã£o ${position} marcado para exclusÃ£o. Clique em Salvar para confirmar.`);
            
            // Esconde a linha mas mantÃ©m no DOM - serÃ¡ excluÃ­da ao salvar
            row.hide();
        }
    });

    // Confirmar exclusÃ£o de nÃ­vel
    $('#confirmDeleteButton').click(function() {
        // Obter dados do modal
        const $row = $('#modalConfirmDelete').data('row');
        const nivelId = $row.data('id');
        
        // Encontra o Ã­ndice no array de dados
        const levelIndex = niveisData.findIndex(nivel => nivel.id == nivelId);
        if (levelIndex >= 0) {
            // Remove do array de dados
            niveisData.splice(levelIndex, 1);
            
            // Atualiza os Ã­ndices de ordem
            niveisData.forEach((nivel, index) => {
                nivel.order = index;
            });
            
            // Renderiza a tabela novamente
            renderNiveisTable();
            
            // Atualiza a tabela de prÃªmios sem resetar as linhas
            updatePremiosTableWithoutReset();
            
            // Reinicializa o drag and drop
            initDragAndDrop();
            
            // Fecha o modal
                    $('#modalConfirmDelete').modal('hide');
                    
            // Notificar o usuÃ¡rio
            toastr.success("NÃ­vel excluÃ­do com sucesso!");
            
            // Reseta o estado de ediÃ§Ã£o, se o nÃ­vel que estava sendo editado foi excluÃ­do
            if (isEditing && editingId == nivelId) {
                resetForm();
                $("#submit-btn").html('<i class="fa fa-plus mr5"></i> Adicionar');
                isEditing = false;
                editingId = null;
            }
                    } else {
            console.error("NÃ­vel nÃ£o encontrado para exclusÃ£o:", nivelId);
            toastr.error("Erro ao excluir nÃ­vel, recarregue a pÃ¡gina e tente novamente.");
                $('#modalConfirmDelete').modal('hide');
            }
    });

    // BotÃ£o para abrir modal de importaÃ§Ã£o
    $("#btn-importar").click(function() {
        // Limpa o input de arquivo
        $('#importFile').val('');
        
        // Abre o modal de importaÃ§Ã£o
        $('#modalImport').modal('show');
    });
    
    // BotÃ£o para confirmar importaÃ§Ã£o
    $('#confirmImportButton').click(function() {
        const fileInput = $('#importFile')[0];
        
        if (!fileInput.files || !fileInput.files[0]) {
            toastr.error('Selecione um arquivo para importar.');
            return;
        }
        
        const file = fileInput.files[0];
        
        if (!file.name.endsWith('.xls') && !file.name.endsWith('.xlsx')) {
            toastr.error('Formato de arquivo invÃ¡lido. Use .xls ou .xlsx');
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
                    toastr.error('O arquivo nÃ£o contÃ©m dados.');
                    return;
                }
                
                // Verifica se as colunas necessÃ¡rias existem
                const firstRow = jsonData[0];
                const requiredColumns = ['NÃ­vel', 'Participantes', 'Craques', 'Dono Craque'];
                const missingColumns = requiredColumns.filter(column => !(column in firstRow));
                
                if (missingColumns.length > 0) {
                    toastr.error('Colunas obrigatÃ³rias ausentes: ' + missingColumns.join(', '));
                    return;
                }
                
                // Pergunta ao usuÃ¡rio se deseja limpar os nÃ­veis existentes
                if ($("#table tbody tr").length > 0) {
                    if (confirm('Deseja substituir os nÃ­veis existentes pelos importados?')) {
                        $("#table tbody").empty();
                    }
                }
                
                // Adiciona os nÃ­veis importados
                let importCount = 0;
                jsonData.forEach(function(row) {
                    if (row['NÃ­vel']) {
                        addLevel(
                            row['NÃ­vel'],
                            row['Participantes'] || 0,
                            row['Craques'] || 0,
                            row['Dono Craque'] === 'Sim' || false,
                            null // NÃ£o importamos imagens do Excel
                        );
                        importCount++;
                    }
                });
                
                updatePremiosTable();
                
                // Fecha o modal
                $('#modalImport').modal('hide');
                
                toastr.success(`${importCount} nÃ­veis importados com sucesso!`);
                
                // Reinicializa o drag and drop apÃ³s importar
                initDragAndDrop();
            } catch (error) {
                console.error(error);
                toastr.error('Erro ao importar arquivo. Verifique o formato!');
            }
        };
        
        reader.readAsArrayBuffer(file);
    });

    // Exportar nÃ­veis
    $("a[title='Exportar']").click(function() {
        const data = [];
        $("#table tbody tr").each(function() {
            const row = $(this);
            data.push({
                'NÃ­vel': row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim(),
                'Participantes': row.find('td:eq(2)').text(),
                'Craques': row.find('td:eq(3)').text(),
                'Dono Craque': row.find('td:eq(4)').text()
            });
        });

        if (data.length === 0) {
            toastr.warning('Nenhum nÃ­vel para exportar!');
            return;
        }

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "NÃ­veis");
        XLSX.writeFile(wb, "futligas_niveis.xlsx");
        toastr.success('NÃ­veis exportados com sucesso!');
    });

    // Adiciona evento para o botÃ£o de adicionar prÃªmio
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
                <td>${position}Â°</td>
                <td class="center-middle">
                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                            <i class="fa fa-plus"></i>
                        </div>
                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                    </div>
                </td>`;
                
        // Adiciona cÃ©lulas para cada nÃ­vel
        niveis.forEach(nivel => {
            newRow += `
                <td>
                    <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                </td>`;
        });
        
        // Finaliza a linha com a cÃ©lula de aÃ§Ãµes - botÃ£o simplificado e maior
        newRow += `
                <td>
                    <button type="button" class="btn btn-danger delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                </td>
            </tr>`;
        
        // Adiciona a linha Ã  tabela
        $premiTable.find('tbody').append(newRow);
        
        // Inicializa o preview de imagem para a nova linha
        initPremioImagePreview($premiTable.find('tbody tr:last'));
        
        // Reaplica os eventos aos botÃµes de exclusÃ£o
        initDeletePremioButtons();
        
        toastr.success('PrÃªmio adicionado com sucesso!');
    });
    
    // FunÃ§Ã£o para inicializar a visualizaÃ§Ã£o de imagem de prÃªmio
    function initPremioImagePreview(row) {
        console.log('[DEBUG-PREMIO] Inicializando visualizaÃ§Ã£o de imagem para prÃªmio');
        
        try {
            // Verifica se a linha existe
            if (!row || row.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Linha para inicializar visualizaÃ§Ã£o de imagem nÃ£o existe');
                return;
            }
            
            const previewContainer = row.find('.premio-image-preview');
            
            // Verifica se o container existe
            if (!previewContainer || previewContainer.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Container .premio-image-preview nÃ£o encontrado na linha');
                console.log('[DEBUG-PREMIO] Estrutura da linha:', row.html());
                return;
            }
            
            const fileInput = row.find('.premio-image');
            
            // Verifica se o input existe
            if (!fileInput || fileInput.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Input .premio-image nÃ£o encontrado na linha');
                return;
            }
            
            console.log('[DEBUG-PREMIO] Container e input encontrados para inicializaÃ§Ã£o');
            
            // Marca o container como inicializado
            previewContainer.data('click-initialized', true);
            
            // Ao clicar no contÃªiner, ativa o input de arquivo
            previewContainer.off('click').on('click', function() {
                console.log('[DEBUG-PREMIO] Clique no container de imagem, ativando input file');
                fileInput.click();
            });
            
            // Ao selecionar um arquivo, exibe a prÃ©-visualizaÃ§Ã£o
            fileInput.off('change').on('change', function(e) {
                console.log('[DEBUG-PREMIO] Arquivo selecionado para imagem do prÃªmio');
                
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
                            console.log('[DEBUG-PREMIO] Removendo imagem do prÃªmio');
                            e.stopPropagation();
                            previewContainer.html('<i class="fa fa-plus"></i>');
                            fileInput.val('');
                        });
                        
                        console.log('[DEBUG-PREMIO] Imagem do prÃªmio carregada e visualizaÃ§Ã£o inicializada');
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
            
            console.log('[DEBUG-PREMIO] VisualizaÃ§Ã£o de imagem para prÃªmio inicializada com sucesso');
        } catch (error) {
            console.error('[DEBUG-PREMIO] ERRO ao inicializar visualizaÃ§Ã£o de imagem:', error);
            console.error('[DEBUG-PREMIO] Stack trace:', error.stack);
        }
    }
    
    // FunÃ§Ã£o para inicializar os botÃµes de exclusÃ£o de prÃªmios
    function initDeletePremioButtons() {
        // Remove handlers anteriores para evitar duplicaÃ§Ã£o
        $('.delete-premio').off('click');
        $(document).off('click', '.delete-premio');
        
        // Adiciona novos handlers
        $(document).on('click', '.delete-premio', function() {
            const row = $(this).closest('tr');
            const prizeId = row.data('id');
            const position = row.find('td:eq(0)').text().trim();
            
            console.log(`[DEBUG-PREMIO] Clique em excluir prÃªmio - ID: ${prizeId}, PosiÃ§Ã£o: ${position}`);
            
            // Atualiza o texto do modal com a posiÃ§Ã£o correta
            $('#levelNameToDelete').text(position);
            
            // Armazena a referÃªncia da linha para ser usada na confirmaÃ§Ã£o
            $('#modalConfirmDelete').data('row-to-delete', row);
            
            // Mostra modal de confirmaÃ§Ã£o para todos os prÃªmios
            $('#modalConfirmDelete').modal('show');
            
            // Configuramos o botÃ£o de confirmaÃ§Ã£o no handler global, fora desta funÃ§Ã£o
        });
    }

    // Configura o handler para o botÃ£o de confirmaÃ§Ã£o de exclusÃ£o no modal
    $('#confirmDeleteButton').off('click').on('click', function() {
        // ObtÃ©m a referÃªncia da linha armazenada
        const row = $('#modalConfirmDelete').data('row-to-delete');
        if (!row) {
            console.error('[DEBUG-PREMIO] ERRO: Nenhuma linha de prÃªmio encontrada para excluir');
            $('#modalConfirmDelete').modal('hide');
            return;
        }
        
        const prizeId = row.data('id');
        const position = row.find('td:eq(0)').text().trim();
        
        console.log(`[DEBUG-PREMIO] Confirmando exclusÃ£o do prÃªmio - ID: ${prizeId}, PosiÃ§Ã£o: ${position}`);
        
        // Fecha o modal
        $('#modalConfirmDelete').modal('hide');
        
        // Mostra indicador de carregamento
        row.find('.delete-premio').html('<i class="fa fa-spinner fa-spin"></i>');
        
        // Se tem ID, adiciona Ã  lista de IDs a serem excluÃ­dos no servidor
        if (prizeId) {
            console.log(`[DEBUG-PREMIO] Adicionando ID ${prizeId} Ã  lista de prÃªmios excluÃ­dos`);
            
            // Adiciona o ID ao array de IDs excluÃ­dos para enviar ao servidor
            if (!deletedPrizeIds.includes(prizeId)) {
                deletedPrizeIds.push(prizeId);
            }
            
            toastr.success('PrÃªmio marcado para exclusÃ£o. Clique em Salvar para confirmar.');
        } else {
            console.log('[DEBUG-PREMIO] Removendo prÃªmio sem ID da tabela');
        }
        
        // Remove a linha da tabela
        row.fadeOut(300, function() {
            $(this).remove();
            updatePrizesPositions();
            console.log(`[DEBUG-PREMIO] PrÃªmio removido da tabela`);
        });
    });

    // FunÃ§Ã£o para atualizar as posiÃ§Ãµes dos prÃªmios apÃ³s exclusÃ£o
    function updatePrizesPositions() {
        console.log('[DEBUG-PREMIO] Atualizando posiÃ§Ãµes dos prÃªmios');
        $('#premiosTable tbody tr').each(function(index) {
            const position = index + 1;
            $(this).find('td:first').text(position + 'Â°');
            $(this).data('position', position);
            console.log(`[DEBUG-PREMIO] Nova posiÃ§Ã£o: ${position} para prÃªmio ID: ${$(this).data('id') || 'Novo'}`);
        });
    }
    
    // Adiciona o HTML do modal ao final do body
    $('body').append(`
        <div class="modal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-labelledby="confirmDeletePrizeModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmDeletePrizeModalLabel">Confirmar ExclusÃ£o</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Fechar">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        Tem certeza que deseja excluir este prÃªmio?
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-danger" id="confirmDeletePrize">Excluir</button>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    // Handler para confirmar a exclusÃ£o
    $('#confirmDeletePrize').on('click', function() {
        const $row = $('#confirmDeletePrizeModal').data('row-to-delete');
        const position = $row.find('td:first').text();
        const prizeId = $row.data('id'); // ObtÃ©m o ID do prÃªmio se existir
        
        console.log('==== EXCLUINDO PRÃŠMIO ====');
        console.log('PosiÃ§Ã£o:', position);
        console.log('ID do prÃªmio:', prizeId);
        console.log('Dados da linha:', $row.data());
        
        // Se o prÃªmio jÃ¡ tem um ID no banco de dados, adiciona ao array de excluÃ­dos
        if (prizeId) {
            deletedPrizeIds.push(prizeId);
            console.log(`Adicionado ID ${prizeId} Ã  lista de prÃªmios a serem excluÃ­dos:`, deletedPrizeIds);
        } else {
            console.log('PrÃªmio nÃ£o tem ID, apenas removendo da interface');
        }
        
        $row.remove();
        
        // Atualiza as posiÃ§Ãµes dos prÃªmios
        $('#premiosTable tbody tr').each(function(index) {
            $(this).find('td:first').text((index + 1) + 'Â°');
        });
        
        // Fecha o modal
        $('#confirmDeletePrizeModal').modal('hide');
        
        toastr.success(`PrÃªmio da posiÃ§Ã£o ${position} excluÃ­do com sucesso!`);
    });

    // Inicializa as visualizaÃ§Ãµes de imagem para os prÃªmios existentes
    $(document).ready(function() {
        // Adiciona o modal de confirmaÃ§Ã£o de exclusÃ£o se ainda nÃ£o existir
        if (!$('#confirmDeletePrizeModal').length) {
            $('body').append(`
                <div class="modal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-labelledby="confirmDeletePrizeModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-sm" role="document">
                        <div class="modal-content">
                            <div class="modal-header bg-danger text-white">
                                <h5 class="modal-title" id="confirmDeletePrizeModalLabel">Confirmar ExclusÃ£o</h5>
                                <button type="button" class="close text-white" data-dismiss="modal" aria-label="Fechar">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                Tem certeza que deseja excluir este prÃªmio?
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Cancelar</button>
                                <button type="button" class="btn btn-danger" id="confirmDeletePrize">Excluir</button>
                            </div>
                        </div>
                    </div>
                </div>
            `);

            // Configura o handler de confirmaÃ§Ã£o apenas uma vez
            $('#confirmDeletePrize').on('click', function() {
                const $row = $('#confirmDeletePrizeModal').data('row-to-delete');
                const position = $row.find('td:first').text();
                const prizeId = $row.data('id'); // ObtÃ©m o ID do prÃªmio se existir
                
                console.log('==== EXCLUINDO PRÃŠMIO ====');
                console.log('PosiÃ§Ã£o:', position);
                console.log('ID do prÃªmio:', prizeId);
                console.log('Dados da linha:', $row.data());
                
                // Se o prÃªmio jÃ¡ tem um ID no banco de dados, adiciona ao array de excluÃ­dos
                if (prizeId) {
                    deletedPrizeIds.push(prizeId);
                    console.log(`Adicionado ID ${prizeId} Ã  lista de prÃªmios a serem excluÃ­dos:`, deletedPrizeIds);
                } else {
                    console.log('PrÃªmio nÃ£o tem ID, apenas removendo da interface');
                }
                
                $row.remove();
                
                // Atualiza as posiÃ§Ãµes dos prÃªmios
                $('#premiosTable tbody tr').each(function(index) {
                    $(this).find('td:first').text((index + 1) + 'Â°');
                });
                
                // Fecha o modal
                $('#confirmDeletePrizeModal').modal('hide');
                
                toastr.success(`PrÃªmio da posiÃ§Ã£o ${position} excluÃ­do com sucesso!`);
            });
        }

        // Inicializa as visualizaÃ§Ãµes de imagem para os prÃªmios existentes
        $('#premiosTable tbody tr').each(function() {
            initPremioImagePreview($(this));
        });
        
        // Inicializa os botÃµes de exclusÃ£o
        initDeletePremioButtons();
    });

    // Salvar todas as configuraÃ§Ãµes
    $("#successToast").off('click').on('click', function(e) {
        e.preventDefault();
        console.log("[DEBUG-PREMIO] ============ INÃCIO DO PROCESSO DE SALVAMENTO ============");
        console.log("[DEBUG-PREMIO] BotÃ£o de salvar clicado");
        
        // Mostra indicador de carregamento
        const $btn = $(this);
        const originalHtml = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin mr5"></i> Salvando...').prop('disabled', true);
        
        try {
            console.log("[DEBUG-PREMIO] Iniciando preparaÃ§Ã£o dos dados dos nÃ­veis");
            
            // Prepara os dados dos nÃ­veis
            const niveis = [];
            $("#table tbody tr").each(function() {
                const row = $(this);
                const id = row.data('id');
                const name = row.find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
                const players = parseInt(row.find('td:eq(2)').text()) || 0;
                const premium_players = parseInt(row.find('td:eq(3)').text()) || 0;
                const owner_premium = row.find('td:eq(4) i.fa-check').length > 0;
                const image = row.find('td:eq(1) img').attr('src');
                
                console.log(`[DEBUG-PREMIO] Processando nÃ­vel: ID=${id}, Nome=${name}`);
                
                niveis.push({
                    id: id,
                    name: name,
                    players: players,
                    premium_players: premium_players,
                    owner_premium: owner_premium,
                    image: image
                });
            });
            
            console.log(`[DEBUG-PREMIO] Total de nÃ­veis coletados: ${niveis.length}`);
            console.log("[DEBUG-PREMIO] Iniciando preparaÃ§Ã£o dos dados dos prÃªmios");
            
            // Verifica se a tabela de prÃªmios existe
            const $premiosTable = $('#premiosTable');
            if ($premiosTable.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Tabela de prÃªmios #premiosTable nÃ£o encontrada!');
                throw new Error('Tabela de prÃªmios nÃ£o encontrada');
            }
            
            console.log(`[DEBUG-PREMIO] Tabela de prÃªmios encontrada, contÃ©m ${$premiosTable.find('tbody tr').length} linhas`);
            
            // Prepara os dados dos prÃªmios
            const premios = [];
            $("#premiosTable tbody tr").each(function(index) {
                try {
                    const row = $(this);
                    console.log(`[DEBUG-PREMIO] Processando linha ${index+1} da tabela de prÃªmios`);
                    
                    // Verifica se a linha tem todos os elementos esperados
                    if (row.find('td').length < 2) {
                        console.error(`[DEBUG-PREMIO] ERRO: Linha ${index+1} nÃ£o tem cÃ©lulas suficientes: ${row.find('td').length}`);
                        return; // Pula esta linha
                    }
                    
                    // Coleta dados bÃ¡sicos
                    const positionText = row.find('td:eq(0)').text().trim();
                    const position = parseInt(positionText) || parseInt(positionText.replace('Â°', '')) || 0;
                    let prizeId = row.data('id');
                    // Converter "null" ou "undefined" em string ou undefined para null
                    if (prizeId === undefined || prizeId === "undefined" || prizeId === "null" || prizeId === null) {
                        prizeId = null;
                    }
                    
                    console.log(`[DEBUG-PREMIO] Dados bÃ¡sicos: PosiÃ§Ã£o=${position}, ID=${prizeId || 'novo'}`);
                    
                    // Verifica e coleta a imagem
                    let image = null;
                    const imgElement = row.find('td:eq(1) img');
                    if (imgElement.length > 0) {
                        image = imgElement.attr('src');
                        console.log(`[DEBUG-PREMIO] Imagem encontrada para prÃªmio posiÃ§Ã£o ${position}`);
                    } else {
                        console.log(`[DEBUG-PREMIO] Sem imagem para prÃªmio posiÃ§Ã£o ${position}`);
                    }
                    
                    // Inicializa objeto values vazio
                    const values = {};
                    
                    // Analisa a estrutura da linha para entender como coletar valores
                    console.log(`[DEBUG-PREMIO] Estrutura da linha: ${row.find('td').length} cÃ©lulas, ${row.find('input.premio-valor').length} inputs de valor`);
                    
                    // MÃ©todo 1: Tenta coletar valores atravÃ©s dos inputs com data-nivel
                    let valorEncontrado = false;
                    row.find('input.premio-valor').each(function() {
                        const $input = $(this);
                        const nivelName = $input.data('nivel');
                        if (nivelName) {
                            valorEncontrado = true;
                            const value = parseInt($input.val()) || 0;
                            values[nivelName] = value;
                            console.log(`[DEBUG-PREMIO] MÃ©todo 1: Valor para nÃ­vel '${nivelName}': ${value}`);
                        } else {
                            console.warn(`[DEBUG-PREMIO] Input sem atributo data-nivel encontrado na posiÃ§Ã£o ${position}`);
                            // Imprime os atributos do input para diagnÃ³stico
                            const attribs = {};
                            $.each($input[0].attributes, function() {
                                if(this.specified) {
                                    attribs[this.name] = this.value;
                                }
                            });
                            console.log('[DEBUG-PREMIO] Atributos do input:', attribs);
                        }
                    });
                    
                    // MÃ©todo 2: Se nÃ£o encontrou valores pelo mÃ©todo 1, tenta pelo Ã­ndice das cÃ©lulas
                    if (!valorEncontrado || Object.keys(values).length === 0) {
                        console.warn(`[DEBUG-PREMIO] MÃ©todo 1 falhou para prÃªmio posiÃ§Ã£o ${position}, tentando mÃ©todo 2`);
                        
                        // Percorre cada nÃ­vel
                        for (let i = 0; i < niveis.length; i++) {
                            const nivel = niveis[i].name;
                            // Ãndice da cÃ©lula: 2 cÃ©lulas base (posiÃ§Ã£o + imagem) + Ã­ndice do nÃ­vel
                            const inputField = row.find(`td:eq(${i + 2}) input`);
                            
                            if (inputField.length) {
                                const value = parseInt(inputField.val()) || 0;
                                values[nivel] = value;
                                console.log(`[DEBUG-PREMIO] MÃ©todo 2: Valor para nÃ­vel '${nivel}': ${value}, cÃ©lula ${i+2}`);
                            } else {
                                console.warn(`[DEBUG-PREMIO] MÃ©todo 2: NÃ£o encontrou input para nÃ­vel '${nivel}' na cÃ©lula ${i+2}`);
                            }
                        }
                    }
                    
                    // MÃ©todo 3: Ãšltimo recurso - verifica todos os inputs na linha
                    if (Object.keys(values).length === 0) {
                        console.warn(`[DEBUG-PREMIO] MÃ©todos 1 e 2 falharam para prÃªmio posiÃ§Ã£o ${position}, tentando mÃ©todo 3`);
                        
                        // Verifica se existem inputs
                        const allInputs = row.find('input[type="number"]');
                        console.log(`[DEBUG-PREMIO] MÃ©todo 3: Encontrados ${allInputs.length} inputs numÃ©ricos na linha`);
                        
                        // Associa os inputs disponÃ­veis aos nÃ­veis na ordem
                        allInputs.each(function(idx) {
                            if (idx < niveis.length) {
                                const nivel = niveis[idx].name;
                                const value = parseInt($(this).val()) || 0;
                                values[nivel] = value;
                                console.log(`[DEBUG-PREMIO] MÃ©todo 3: Associando input #${idx+1} ao nÃ­vel '${nivel}': ${value}`);
                            }
                        });
                    }
                    
                    // Valida se temos valores para pelo menos um nÃ­vel
                    if (Object.keys(values).length === 0) {
                        console.error(`[DEBUG-PREMIO] ALERTA: PrÃªmio posiÃ§Ã£o ${position} nÃ£o tem valores definidos apÃ³s tentar 3 mÃ©todos!`);
                        
                        // Valores padrÃ£o para cada nÃ­vel como Ãºltimo recurso
                        niveis.forEach(nivel => {
                            values[nivel.name] = 1000;
                            console.log(`[DEBUG-PREMIO] Definindo valor padrÃ£o 1000 para nÃ­vel '${nivel.name}'`);
                        });
                    }
                    
                    // Agora sim, adiciona o prÃªmio ao array
                    premios.push({
                        id: prizeId === undefined || prizeId === "undefined" || prizeId === "null" ? null : prizeId,
                        position: position,
                        image: image,
                        values: values,
                        league_id: 6 // Adicionando o league_id fixo com valor 6, conforme visto no banco de dados
                    });
                    
                    console.log(`[DEBUG-PREMIO] PrÃªmio preparado - PosiÃ§Ã£o: ${position}, ID: ${prizeId || 'novo'}, Valores: ${Object.keys(values).length}`);
                } catch (rowError) {
                    console.error(`[DEBUG-PREMIO] Erro ao processar linha ${index+1} da tabela de prÃªmios:`, rowError);
                }
            });
            
            console.log(`[DEBUG-PREMIO] Total de prÃªmios preparados: ${premios.length}`);
            
            // Log detalhado de cada prÃªmio
            premios.forEach((premio, index) => {
                console.log(`[DEBUG-PREMIO] Detalhes do prÃªmio ${index+1}:`, {
                    id: premio.id,
                    position: premio.position,
                    hasImage: !!premio.image,
                    valuesCount: Object.keys(premio.values).length,
                    values: premio.values
                });
            });
            
            console.log(`[DEBUG-PREMIO] Total de prÃªmios marcados para exclusÃ£o: ${deletedPrizeIds.length}`);
            
            // Prepara os dados de premiaÃ§Ã£o
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
            
            // Adiciona os IDs dos prÃªmios excluÃ­dos aos dados
            const dadosCompletos = {
                levels: niveis,
                prizes: premios,
                award_config: premiacao,
                deleted_prize_ids: deletedPrizeIds
            };
            
            // Backup em localStorage antes de enviar
            try {
                localStorage.setItem('premiosBackup', JSON.stringify(premios));
                console.log("[DEBUG-PREMIO] Backup de prÃªmios salvo no localStorage");
            } catch (e) {
                console.error("[DEBUG-PREMIO] Erro ao fazer backup dos prÃªmios:", e);
            }
            
            console.log("[DEBUG-PREMIO] Preparando envio dos dados para o servidor");
            
            // Imprime cada seÃ§Ã£o dos dados para verificaÃ§Ã£o
            console.log(`[DEBUG-PREMIO] Dados completos - nÃ­veis: ${niveis.length}, prÃªmios: ${premios.length}, exclusÃµes: ${deletedPrizeIds.length}`);
            
            // Verifica se hÃ¡ dados vÃ¡lidos para enviar
            if (premios.length === 0) {
                console.warn("[DEBUG-PREMIO] Nenhum prÃªmio encontrado para enviar");
            }
            
            console.log("[DEBUG-PREMIO] URL de destino: /futligas/jogadores/salvar/");
            
            // Faz a requisiÃ§Ã£o AJAX
            $.ajax({
                url: '/futligas/jogadores/salvar/',
                method: 'POST',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                data: JSON.stringify(dadosCompletos),
                contentType: 'application/json',
                success: function(response) {
                    console.log("[DEBUG-PREMIO] Resposta do servidor:", response);
                    if (response.success) {
                        toastr.success('Dados salvos com sucesso!');
                        console.log("[DEBUG-PREMIO] Limpando array de prÃªmios excluÃ­dos apÃ³s sucesso");
                        deletedPrizeIds = [];
                        
                        // Recarrega os dados apÃ³s salvar com sucesso
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    } else {
                        console.error("[DEBUG-PREMIO] Erro retornado pelo servidor:", response.message || 'Erro desconhecido');
                        toastr.error(response.message || 'Erro ao salvar dados');
                        $btn.html(originalHtml).prop('disabled', false);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("[DEBUG-PREMIO] Erro na requisiÃ§Ã£o AJAX:", {
                        status: status,
                        error: error,
                        response: xhr.responseText
                    });
                    
                    // Tenta analisar a resposta para obter mais detalhes
                    try {
                        const respJson = JSON.parse(xhr.responseText);
                        console.error("[DEBUG-PREMIO] Detalhes do erro:", respJson);
                    } catch (e) {
                        console.error("[DEBUG-PREMIO] NÃ£o foi possÃ­vel analisar a resposta:", xhr.responseText);
                    }
                    
                    toastr.error('Erro ao salvar dados');
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

    // FunÃ§Ãµes auxiliares
    function addLevel(name, players, premium_players, owner_premium, imageData = null) {
        console.log("Adicionando novo nÃ­vel:", name);
        
        // Gerar um ID Ãºnico temporÃ¡rio atÃ© que o nÃ­vel seja salvo no servidor
        const id = 'temp_' + Date.now();
        
        // Backup das imagens existentes antes de qualquer modificaÃ§Ã£o
        const imagensBackup = {};
        niveisData.forEach(nivel => {
            if (nivel.image) {
                imagensBackup[nivel.id] = nivel.image;
            }
        });
        
        // Garante que os dados da imagem sejam vÃ¡lidos
        if (imageData === undefined) {
            console.log("Corrigindo undefined para imageData");
            imageData = null;
        }
        
        // Cria o objeto de nÃ­vel completo
        const newLevel = {
            id: id,
            name: name,
            players: parseInt(players) || 0,
            premium_players: parseInt(premium_players) || 0,
            owner_premium: !!owner_premium,
            image: imageData,
            order: niveisData.length
        };
        
        console.log("Objeto de nÃ­vel criado:", newLevel);
        console.log("Tem imagem:", newLevel.image ? "Sim" : "NÃ£o");
        
        // Adiciona aos dados em memÃ³ria
        niveisData.push(newLevel);
        
        // Restaura as imagens do backup para os nÃ­veis existentes
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
        
        // Renderiza a tabela com o novo nÃ­vel
        renderNiveisTable();
        
        // Atualiza a tabela de prÃªmios sem perder os dados existentes
        updatePremiosTableWithoutReset();
        
        // Reinicializa o drag and drop apÃ³s adicionar nova linha
        initDragAndDrop();
    }
    
    // Nova funÃ§Ã£o para atualizar a tabela de prÃªmios sem resetar/recriar todas as linhas
    function updatePremiosTableWithoutReset() {
        console.log("Iniciando updatePremiosTableWithoutReset");
        
        // ObtÃ©m a lista de nÃ­veis disponÃ­veis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        console.log("NÃ­veis disponÃ­veis para atualizaÃ§Ã£o:", niveis);
        
        // Verifica se a tabela tem o seletor correto
        const $premiosTable = $('#premiosTable');
        
        // Verifica quantas posiÃ§Ãµes existem
        let premioRows = $premiosTable.find('tbody tr').length;
        console.log(`NÃºmero de linhas de prÃªmios existentes: ${premioRows}`);
        
        // CORREÃ‡ÃƒO: NÃ£o force a criaÃ§Ã£o de linhas de prÃªmios durante atualizaÃ§Ãµes
        // SÃ³ crie linhas se nÃ£o houver nenhuma e nÃ£o houver sido inicializado ainda
        if (premioRows === 0 && !window.premiosInitialized) {
            console.log("Sem linhas de prÃªmio e sem inicializaÃ§Ã£o prÃ©via - chamando updatePremiosTable");
            updatePremiosTable();
            return;
        }

        // Atualiza os cabeÃ§alhos da tabela para incluir os nÃ­veis
        const premiosHeader = $premiosTable.find('thead tr');
        
        // Guarda os nÃ­veis que jÃ¡ estÃ£o na tabela
        const niveisExistentes = [];
        premiosHeader.find('th[data-nivel]').each(function() {
            niveisExistentes.push($(this).attr('data-nivel'));
        });
        console.log("NÃ­veis existentes na tabela:", niveisExistentes);
        
        // Remove colunas de nÃ­veis que nÃ£o existem mais
        premiosHeader.find('th[data-nivel]').each(function() {
            const nivel = $(this).attr('data-nivel');
            if (!niveis.includes(nivel)) {
                console.log(`Removendo coluna do nÃ­vel '${nivel}' que nÃ£o existe mais`);
                const index = $(this).index();
                $premiosTable.find(`tbody tr`).each(function() {
                    $(this).find(`td:eq(${index})`).remove();
                });
                $(this).remove();
            }
        });
        
        // Adiciona colunas para novos nÃ­veis
        for (let i = 0; i < niveis.length; i++) {
            const nivel = niveis[i];
            if (!niveisExistentes.includes(nivel)) {
                console.log(`Adicionando nova coluna para o nÃ­vel '${nivel}'`);
                premiosHeader.find('th:last').before(`<th class="per15" data-nivel="${nivel}">${nivel}</th>`);
                
                // Adiciona cÃ©lulas para este nÃ­vel em todas as linhas
                $premiosTable.find('tbody tr').each(function() {
                    const $actionCell = $(this).find('td:last');
                    $actionCell.before(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                        </td>`);
                });
            }
        }

        // Verificar se as imagens estÃ£o sendo exibidas corretamente
        $premiosTable.find('tbody tr').each(function(index) {
            const $row = $(this);
            const $imageCell = $row.find('td:eq(1)');
            
            // Verifica se a cÃ©lula de imagem tem conteÃºdo
            if ($imageCell.find('img').length === 0 && $imageCell.find('.premio-image-preview').length === 0) {
                console.log(`Corrigindo cÃ©lula de imagem na linha ${index + 1}`);
                $imageCell.html(`
                    <div class="premio-image-container" style="position: relative; display: inline-block;">
                        <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                            <i class="fa fa-plus"></i>
                        </div>
                        <input type="file" class="premio-image" style="display: none;" accept="image/*">
                    </div>
                `);
                
                // Inicializa o preview para esta linha
                initPremioImagePreview($row);
            }
            
            // Verifica se a cÃ©lula de aÃ§Ã£o tem o botÃ£o de exclusÃ£o
            const $actionCell = $row.find('td:last');
            if ($actionCell.find('.delete-premio').length === 0) {
                console.log(`Adicionando botÃ£o de exclusÃ£o na linha ${index + 1}`);
                $actionCell.html(`
                    <button type="button" class="btn btn-danger delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                `);
            }
        });
        
        // Inicializa os botÃµes de exclusÃ£o para garantir que funcionem
        initDeletePremioButtons();
        
        // Marca como inicializado se nÃ£o estiver jÃ¡
        window.premiosInitialized = true;
        
        console.log("updatePremiosTableWithoutReset concluÃ­do com sucesso");
    }

    function updateLevel(id, name, players, premium_players, owner_premium, imageData = null) {
        console.log(`Atualizando nÃ­vel ID ${id} - Nome: ${name}`);
        
        // Backup das imagens existentes
        const imagensBackup = {};
        niveisData.forEach(nivel => {
            if (nivel.image) {
                imagensBackup[nivel.id] = nivel.image;
            }
        });
        
        // Encontra o nÃ­vel nos dados em memÃ³ria
        const levelIndex = niveisData.findIndex(nivel => nivel.id == id);
        if (levelIndex >= 0) {
            // Preserva os dados atuais para comparaÃ§Ã£o
            const nivelAntigo = {...niveisData[levelIndex]};
            console.log("Dados anteriores:", nivelAntigo);
            console.log("Imagem anterior:", nivelAntigo.image ? "Sim" : "NÃ£o");
            console.log("Nova imagem:", imageData ? "Sim" : "NÃ£o");
            
            // Determina qual imagem usar
            let imagemFinal = imageData;
            
            // Se nÃ£o foi fornecida uma nova imagem (null/undefined) E nÃ£o houve remoÃ§Ã£o explÃ­cita,
            // mantÃ©m a imagem existente
            if ((imageData === null || imageData === undefined) && !imageWasRemoved && nivelAntigo.image) {
                console.log("Mantendo imagem existente");
                imagemFinal = nivelAntigo.image;
            } else if (imageWasRemoved) {
                console.log("Imagem foi removida explicitamente");
                imagemFinal = null;
            }
            
            // Atualiza os dados em memÃ³ria preservando a ordem e outras propriedades
            niveisData[levelIndex] = {
                ...nivelAntigo,
                name: name,
                players: parseInt(players) || 0,
                premium_players: parseInt(premium_players) || 0,
                owner_premium: !!owner_premium,
                image: imagemFinal
            };
            
            // Restaura as imagens do backup para os outros nÃ­veis
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
            
            // Atualiza a tabela de prÃªmios sem resetar as linhas
            updatePremiosTableWithoutReset();
            
            // Reinicializa o drag and drop
            initDragAndDrop();
            
            // Limpa o campo de imagem e o preview
            $("#image").val('');
            $("#image-preview").html('<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>');
            
            // Reset imageWasRemoved flag
            imageWasRemoved = false;
        } else {
            console.error("NÃ­vel nÃ£o encontrado para atualizar:", id);
            toastr.error("Erro ao atualizar nÃ­vel. O nÃ­vel nÃ£o foi encontrado.");
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
        
        // Resetar o flag de remoÃ§Ã£o de imagem
        imageWasRemoved = false;
        
        // Revincula eventos no input de imagem
        $("#image").off().on('change', function() {
            const file = this.files[0];
            if (file) {
                // ValidaÃ§Ãµes
                if (!file.type.match('image.*')) {
                    toastr.error('Por favor, selecione uma imagem vÃ¡lida');
                    this.value = '';
                    return;
                }

                if (file.size > 2 * 1024 * 1024) {
                    toastr.error('A imagem nÃ£o pode ter mais que 2MB');
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
                    
                    // Adiciona handler para o botÃ£o de remover
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
        // Atualiza a ordem dos nÃ­veis
        $("#table tbody tr").each(function(index) {
            $(this).attr('data-order', index + 1);
        });
        
        // Atualiza a tabela de prÃªmios quando a ordem dos nÃ­veis muda
        updatePremiosTable();
    }

    function updatePremiosTable() {
        // ObtÃ©m a lista de nÃ­veis disponÃ­veis
        const niveis = [];
        $("#table tbody tr").each(function() {
            niveis.push($(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim());
        });
        console.log("NÃ­veis disponÃ­veis:", niveis);
        
        // Verifica se a tabela tem o seletor correto
        const $premiosTable = $('#premiosTable');
        
        // CORREÃ‡ÃƒO: Verificar se estamos em carregamento inicial ou atualizaÃ§Ã£o
        // SÃ³ criar as 3 posiÃ§Ãµes iniciais durante o carregamento inicial, nÃ£o em atualizaÃ§Ãµes
        const isInitialLoad = !window.premiosInitialized;
        
        // Verifica quantas posiÃ§Ãµes existem
        let premioRows = $premiosTable.find('tbody tr').length;
        if (premioRows === 0 && isInitialLoad) {
            console.log("Primeira inicializaÃ§Ã£o - criando linhas de prÃªmios padrÃ£o");
            // Adiciona pelo menos 3 posiÃ§Ãµes se nÃ£o houver nenhuma e for o carregamento inicial
            for (let i = 1; i <= 3; i++) {
                $premiosTable.find('tbody').append(`
                    <tr data-position="${i}">
                        <td>${i}Â°</td>
                        <td class="center-middle">
                            <div class="premio-image-container" style="position: relative; display: inline-block;">
                                <div class="premio-image-preview dropzone-imagem" style="height: 32px; width: 32px; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                    <i class="fa fa-plus"></i>
                                </div>
                                <input type="file" class="premio-image" style="display: none;" accept="image/*">
                            </div>
                        </td>`);
            
                // Adiciona colunas para cada nÃ­vel
                niveis.forEach(nivel => {
                    $premiosTable.find('tbody tr:last').append(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                        </td>
                    `);
                });
                
                // Adiciona coluna de aÃ§Ãµes com Ã­cone de lixeira bem visÃ­vel
                $premiosTable.find('tbody tr:last').append(`
                        <td>
                        <button type="button" class="btn btn-danger btn-xs delete-premio" title="Excluir"><i class="glyphicon glyphicon-trash"></i></button>
                        </td>
                `);
            }
            premioRows = 3;
            
            // Inicializa os eventos de upload de imagem e botÃµes de exclusÃ£o
            $premiosTable.find('tbody tr').each(function() {
                initPremioImagePreview($(this));
            });
            initDeletePremioButtons();
            
            // Marca que a inicializaÃ§Ã£o foi feita
            window.premiosInitialized = true;
        }

        // Atualiza os cabeÃ§alhos da tabela para incluir os nÃ­veis
        const premiosHeader = $premiosTable.find('thead tr');
        premiosHeader.find('th:gt(1):not(:last)').remove(); // Remove colunas de nÃ­veis existentes
        
        // Adiciona cabeÃ§alhos para cada nÃ­vel
        niveis.forEach(nivel => {
            premiosHeader.find('th:last').before(`<th class="per15" data-nivel="${nivel}">${nivel}</th>`);
        });

        // Atualiza cada linha existente para incluir cÃ©lulas para cada nÃ­vel
        $premiosTable.find('tbody tr').each(function() {
            const $row = $(this);
            const existingNiveis = [];
            
            // Identifica os nÃ­veis jÃ¡ existentes na linha
            $row.find('.premio-valor').each(function() {
                existingNiveis.push($(this).data('nivel'));
            });
            
            // Remove as cÃ©lulas de nÃ­vel que nÃ£o existem mais
            $row.find('td:gt(1):not(:last)').each(function() {
                const $cell = $(this);
                const $input = $cell.find('.premio-valor');
                
                if ($input.length && !niveis.includes($input.data('nivel'))) {
                    $cell.remove();
                }
            });
            
            // Adiciona cÃ©lulas para novos nÃ­veis
            niveis.forEach(nivel => {
                if (!existingNiveis.includes(nivel)) {
                    $row.find('td:last').before(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel}" value="1000" min="0">
                        </td>
                    `);
                }
            });
        });
    }

    // FunÃ§Ã£o para atualizar a interface com dados do servidor
    function updateUIWithServerData(data) {
        console.log("Atualizando interface com dados do servidor:", data);
        
        // Limpa a tabela de nÃ­veis
        $('#table tbody').empty();
        
        // Adiciona nÃ­veis Ã  tabela
        data.levels.forEach(nivel => {
            const newRow = $('<tr>')
                .attr('data-id', nivel.id)
                .attr('data-order', nivel.order)
                .addClass('nivel-row');

            // Adiciona cÃ©lulas da linha
            const nomeHTML = `
                <span class="handle" style="cursor: grab;"><i class="fa fa-bars"></i></span> ${nivel.name}
            `;

            newRow.append($('<td>').html(nomeHTML));
            
            // CÃ©lula de imagem
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
            
            // CÃ©lulas de jogadores e craques
            newRow.append($('<td>').text(nivel.players));
            newRow.append($('<td>').text(nivel.premium_players));
            
            // CÃ©lula de dono craque
            const donoCraque = $('<td>').addClass('center-middle');
            if (nivel.owner_premium) {
                donoCraque.html('<i class="fa fa-check text-success"></i>');
            } else {
                donoCraque.html('<i class="fa fa-times text-danger"></i>');
            }
            newRow.append(donoCraque);
            
            // CÃ©lula de aÃ§Ãµes
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
            
            // Adiciona linha Ã  tabela
            $('#table tbody').append(newRow);
        });
        
        // Limpa tabela de prÃªmios
        $('#premios table tbody').empty();
        
        // Adiciona prÃªmios
        if (data.prizes && data.prizes.length > 0) {
            console.log("Atualizando tabela de prÃªmios com", data.prizes.length, "prÃªmios");
            
            data.prizes.forEach(premio => {
                console.log(`Criando linha para o prÃªmio posiÃ§Ã£o ${premio.position}, ID=${premio.id}`);
                
                const newRow = $(`
                    <tr data-position="${premio.position}" ${premio.id ? `data-id="${premio.id}"` : ''}>
                        <td>${premio.position}Â°</td>
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
                
                // Adiciona cÃ©lulas para cada nÃ­vel
                data.levels.forEach(nivel => {
                    const valorPremio = premio.values && premio.values[nivel.name] !== undefined ? premio.values[nivel.name] : 1000;
                    
                    newRow.append(`
                        <td>
                            <input type="number" class="form-control premio-valor" data-nivel="${nivel.name}" value="${valorPremio}" min="0">
                        </td>
                    `);
                });
                
                // Adiciona coluna de aÃ§Ãµes
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
                
                console.log(`Criada linha para o prÃªmio posiÃ§Ã£o ${premio.position}, ID=${premio.id}`);
            });
        }
        
        // Inicializa eventos para imagens de prÃªmios
        $('#premios table .dropzone-imagem').each(function() {
            $(this).on('click', function() {
                $(this).siblings('input[type="file"]').click();
            });
        });
    }

    // FunÃ§Ã£o para lidar com o clique na dropzone
    window.handleDropzoneClick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Armazena a cÃ©lula atual para uso posterior
        const currentCell = $(this).closest('td');
        
        // Cria um ID Ãºnico para o input temporÃ¡rio
        const tempInputId = 'temp-file-input-' + Date.now();
        
        // Remove qualquer input temporÃ¡rio existente
        $('.temp-file-input').remove();
        
        // Cria um input de arquivo oculto
        const fileInput = $('<input type="file" class="temp-file-input" id="' + tempInputId + '" accept="image/*" style="display:none;">');
        $('body').append(fileInput);
        
        // Define um timeout para remover o input se nÃ£o for usado
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
                    // Cria a visualizaÃ§Ã£o da imagem com o botÃ£o de remover
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
                    
                    // Adiciona evento ao botÃ£o de remover
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
    
    // DelegaÃ§Ã£o de evento para o botÃ£o de remover imagem
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

    // Ajuste para o plugin de importaÃ§Ã£o de Excel
    $('#importFile').on('change', function() {
        const file = this.files[0];
        if (file) {
            const filename = file.name;
            $(this).closest('.input-group').find('input[type="text"]').val(filename);
        }
    });

    // FunÃ§Ã£o para reinicializar o estado do modal
    function resetModalState() {
        // Limpa os dados armazenados no modal
        $('#modalConfirmDelete').removeData('row');
        
        // Garante que o botÃ£o de confirmaÃ§Ã£o esteja habilitado e com texto correto
        $('#confirmDeleteButton').prop('disabled', false).html('Excluir');
    }
    
    // Quando o modal Ã© fechado, reinicia seu estado
    $('#modalConfirmDelete').on('hidden.bs.modal', function() {
        resetModalState();
        
        // Verifica se hÃ¡ backdrop residual e remove
        if ($('.modal-backdrop').length) {
            $('.modal-backdrop').remove();
        }
        
        // Garante que o body nÃ£o tenha a classe modal-open se nÃ£o houver modais abertos
        if ($('.modal.in').length === 0) {
            $('body').removeClass('modal-open');
        }
    });

    // FunÃ§Ã£o para criar o html do botÃ£o de remoÃ§Ã£o de imagem
    function createImagePreviewWithRemoveButton(imageUrl) {
        return `
            <img src="${imageUrl}" style="max-width: 50px; max-height: 50px; object-fit: contain; cursor: pointer;" onclick="document.getElementById('image').click()">
            <button type="button" class="btn btn-danger btn-xs img-remove-btn" id="remove_image_btn" style="position: absolute; bottom: 0; right: 0; background-color: #f8f8f8; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                            <i class="fa fa-trash" style="font-size: 10px; color: #FF5252;"></i>
            </button>
        `;
    }

    // FunÃ§Ã£o para criar o html do preview padrÃ£o sem imagem
    function createDefaultImagePreview() {
        return '<i class="fa fa-file-image-o" style="font-size: 32px; color: #ccc; cursor: pointer;" onclick="document.getElementById(\'image\').click()"></i>';
    }

    // Ajuste do problema de AJAX - garante que as URLs sÃ£o corretas
    $(document).ajaxSend(function(event, jqxhr, options) {
        // Logs para debug
        console.log("URL da requisiÃ§Ã£o antes:", options.url);
        
        // Remover possÃ­veis prefixos em URLs absolutas
        if (options.url && options.url.startsWith('/administrativo')) {
            options.url = options.url.replace('/administrativo', '');
            console.log("URL corrigida:", options.url);
        }
        
        console.log("URL da requisiÃ§Ã£o apÃ³s ajuste:", options.url);
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

    // FunÃ§Ã£o para verificar se URLs requerem ajuste (usando jQuery)
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

    // Inicializa os botÃµes de exclusÃ£o de prÃªmios
    initDeletePremioButtons();

    // ... existing code ...
            // Registra estado atual das imagens de cada nÃ­vel
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
                
                console.log(`[DIAGNÃ“STICO-IMAGEM] PRÃ‰-SALVAMENTO: NÃ­vel ID=${nivelId}, Nome=${nivelNome}, Tem imagem=${temImagem}`);
            });
            
    // Adiciona o modal de confirmaÃ§Ã£o de exclusÃ£o
    if (!$('#confirmDeletePrizeModal').length) {
        $('body').append(`
            <div class="modal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-labelledby="confirmDeletePrizeModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-sm" role="document">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title" id="confirmDeletePrizeModalLabel">Confirmar ExclusÃ£o</h5>
                            <button type="button" class="close text-white" data-dismiss="modal" aria-label="Fechar">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            Tem certeza que deseja excluir este prÃªmio?
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

    // Inicializa as visualizaÃ§Ãµes de imagem para os prÃªmios existentes
    $('#premiosTable tbody tr').each(function() {
        initPremioImagePreview($(this));
    });
    
    // Inicializa os botÃµes de exclusÃ£o
    initDeletePremioButtons();

    // ... existing code ...

    // Handler para o botÃ£o de adicionar prÃªmio
    $('.btn-adicionar-premio').off('click').on('click', function() {
        console.log('[DEBUG-PREMIO] ============ INICIANDO ADIÃ‡ÃƒO DE PRÃŠMIO ============');
        console.log('[DEBUG-PREMIO] BotÃ£o adicionar prÃªmio clicado');
        
        try {
            // ObtÃ©m a lista de nÃ­veis disponÃ­veis
            const niveis = [];
            $("#table tbody tr").each(function() {
                const nivelNome = $(this).find('td:eq(0)').text().replace(/^\s*\u2630\s*/, '').trim();
                niveis.push(nivelNome);
            });
            
            console.log('[DEBUG-PREMIO] NÃ­veis disponÃ­veis para o novo prÃªmio:', niveis);
            
            // Verifica se hÃ¡ nÃ­veis disponÃ­veis
            if (niveis.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Tentativa de adicionar prÃªmio sem nÃ­veis definidos');
                toastr.error('NÃ£o Ã© possÃ­vel adicionar prÃªmios sem nÃ­veis definidos. Adicione pelo menos um nÃ­vel primeiro.');
                return;
            }
            
            // Verifica se o seletor aponta para a tabela correta
            const $premiosTable = $('#premiosTable');
            if ($premiosTable.length === 0) {
                console.error('[DEBUG-PREMIO] ERRO: Tabela de prÃªmios #premiosTable nÃ£o encontrada!');
                toastr.error('Erro ao encontrar a tabela de prÃªmios.');
                return;
            }
            
            console.log(`[DEBUG-PREMIO] Tabela de prÃªmios encontrada, estrutura: cabeÃ§alho=${$premiosTable.find('thead th').length} colunas, corpo=${$premiosTable.find('tbody tr').length} linhas`);
            
            // Valida a estrutura da tabela
            if ($premiosTable.find('thead th').length < 3) { // Pelo menos posiÃ§Ã£o, imagem e uma coluna de aÃ§Ã£o
                console.error('[DEBUG-PREMIO] ERRO: Estrutura do cabeÃ§alho da tabela invÃ¡lida:', $premiosTable.find('thead th').length);
                toastr.error('Estrutura da tabela de prÃªmios invÃ¡lida.');
                return;
            }
            
            // Calcula prÃ³xima posiÃ§Ã£o
            const nextPosition = $premiosTable.find('tbody tr').length + 1;
            console.log(`[DEBUG-PREMIO] Adicionando prÃªmio na posiÃ§Ã£o ${nextPosition}`);
            
            // Criar uma nova linha como elemento jQuery
            const $newRow = $('<tr>')
                .attr('data-position', nextPosition);
            
            // Adicionar cÃ©lula de posiÃ§Ã£o
            $newRow.append($('<td>').text(`${nextPosition}Â°`));
            
            // Adicionar cÃ©lula de imagem
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
            
            console.log(`[DEBUG-PREMIO] CÃ©lulas de posiÃ§Ã£o e imagem adicionadas`);
            
            // Adicionar cÃ©lulas para cada nÃ­vel
            console.log(`[DEBUG-PREMIO] Adicionando cÃ©lulas para ${niveis.length} nÃ­veis`);
            
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
                
                console.log(`[DEBUG-PREMIO] Adicionada cÃ©lula para nÃ­vel '${nivel}' na posiÃ§Ã£o ${idx+1}`);
            });
            
            // Adicionar cÃ©lula de aÃ§Ãµes
            const $actionsCell = $('<td>');
            const $deleteButton = $('<button>').attr({
                type: 'button',
                class: 'btn btn-danger btn-xs delete-premio',
                title: 'Excluir'
            }).append($('<i>').addClass('glyphicon glyphicon-trash'));
            
            $actionsCell.append($deleteButton);
            $newRow.append($actionsCell);
            
            console.log(`[DEBUG-PREMIO] CÃ©lula de aÃ§Ãµes adicionada`);
            console.log(`[DEBUG-PREMIO] Nova linha criada com ${$newRow.find('td').length} cÃ©lulas`);
            
            // Validar se a linha tem o nÃºmero correto de cÃ©lulas
            const expectedCells = 2 + niveis.length + 1; // posiÃ§Ã£o + imagem + nÃ­veis + aÃ§Ãµes
            if ($newRow.find('td').length !== expectedCells) {
                console.error(`[DEBUG-PREMIO] ERRO: NÃºmero incorreto de cÃ©lulas na nova linha: ${$newRow.find('td').length}, esperado: ${expectedCells}`);
            }
            
            // Adicionar a linha Ã  tabela
            $premiosTable.find('tbody').append($newRow);
            
            console.log(`[DEBUG-PREMIO] Linha adicionada Ã  tabela`);
            
            // Verificar se os atributos data-nivel foram definidos corretamente
            $newRow.find('input.premio-valor').each(function(idx) {
                const $input = $(this);
                const nivel = $input.data('nivel');
                console.log(`[DEBUG-PREMIO] Input #${idx+1} - data-nivel="${nivel}"`);
                
                if (!nivel) {
                    console.error(`[DEBUG-PREMIO] ERRO: Atributo data-nivel nÃ£o definido para input #${idx+1}`);
                }
            });
            
            // Inicializar manipulador para upload de imagem
            initPremioImagePreview($newRow);
            
            // Reaplica os eventos aos botÃµes de exclusÃ£o
            initDeletePremioButtons();
            
            console.log('[DEBUG-PREMIO] Novo prÃªmio adicionado com sucesso');
            console.log('[DEBUG-PREMIO] ============ FIM DA ADIÃ‡ÃƒO DE PRÃŠMIO ============');
            
            toastr.success('PrÃªmio adicionado com sucesso!');
        } catch (error) {
            console.error('[DEBUG-PREMIO] ERRO durante a adiÃ§Ã£o de prÃªmio:', error);
            console.error('[DEBUG-PREMIO] Stack trace:', error.stack);
            toastr.error('Erro ao adicionar prÃªmio. Verifique o console para mais detalhes.');
        }
    });

    // Garante que o modal de confirmaÃ§Ã£o de exclusÃ£o exista no DOM
    if ($('#confirmDeletePrizeModal').length === 0) {
        console.log('[DEBUG-PREMIO] Criando modal de confirmaÃ§Ã£o de exclusÃ£o');
        $('body').append(`
            <div class="modal inmodal fade" id="confirmDeletePrizeModal" tabindex="-1" role="dialog" aria-hidden="true">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Fechar</span></button>
                            <h4 class="modal-title">Confirmar ExclusÃ£o</h4>
                        </div>
                        <div class="modal-body">
                            <p>Tem certeza que deseja excluir este prÃªmio?</p>
                            <p class="text-danger">Esta aÃ§Ã£o nÃ£o poderÃ¡ ser desfeita.</p>
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
});
