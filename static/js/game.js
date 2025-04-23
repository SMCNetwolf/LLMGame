document.addEventListener('DOMContentLoaded', function() {
    const commandForm = document.getElementById('commandForm');
    const commandInput = document.getElementById('commandInput');
    const gameText = document.getElementById('gameText');
    const gameImage = document.getElementById('gameImage');
    const loadingOverlay = document.querySelector('.image-loading-overlay');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const playIntroButton = document.getElementById('playIntroButton');
    const audioIntroPlayer = document.getElementById('audioIntroPlayer');
    const audioIntroContainer = document.getElementById('audioIntroContainer');
    const audioIntroText = document.getElementById('audioIntroText');
    
    // Focus input field on page load
    commandInput.focus();
    
    // Handle command form submission
    commandForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const command = commandInput.value.trim();
        if (command === '') return;
        
        // Add user command to game text
        appendToGameText(`> ${command}`, 'user-command');
        
        // Show loading state
        loadingOverlay.classList.remove('d-none');
        
        // Send command to backend
        sendCommand(command);
        
        // Clear input
        commandInput.value = '';
    });
    
    // Handle suggestion clicks
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function() {
            commandInput.value = this.textContent;
            commandInput.focus();
        });
    });
    
    // Function to send command to server
    function sendCommand(command) {
        const formData = new FormData();
        formData.append('command', command);
        
        fetch('/command', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Resposta da rede não foi ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading state
            loadingOverlay.classList.add('d-none');
            
            // Update game text with response
            appendToGameText(data.description, 'game-response');
            
            // Update game image
            gameImage.src = data.image_url;
            
            // Auto-scroll to bottom of game text
            gameText.scrollTop = gameText.scrollHeight;
            
            // Atualizar a música de fundo se a localização mudou
            if (data.current_location && window.audioManager) {
                window.audioManager.playLocationMusic(data.current_location);
                // Atualizar o estado do jogo
                gameState.currentLocation = data.current_location;
            }
            
            // Exibir dicas contextuais se disponíveis
            if (data.hint) {
                showContextualHint(data.hint);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            loadingOverlay.classList.add('d-none');
            appendToGameText('Erro ao processar seu comando. Por favor, tente novamente.', 'error-message');
        });
    }
    
    // Function to append text to game output
    function appendToGameText(text, className) {
        const paragraph = document.createElement('p');
        paragraph.textContent = text;
        paragraph.classList.add(className);
        paragraph.classList.add('fade-in');
        gameText.appendChild(paragraph);
        
        // Auto-scroll to bottom
        gameText.scrollTop = gameText.scrollHeight;
    }
    
    // Image error handling
    gameImage.addEventListener('error', function() {
        this.src = '/static/placeholder.svg';
    });
    
    // Handle game image loading
    gameImage.addEventListener('load', function() {
        loadingOverlay.classList.add('d-none');
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Focus command input when pressing '/' key
        if (e.key === '/' && document.activeElement !== commandInput) {
            e.preventDefault();
            commandInput.focus();
        }
    });
    
    // Função para exibir dicas contextuais
    function showContextualHint(hintText) {
        // Verifica se já existe um toast de dica
        let hintToast = document.getElementById('contextualHintToast');
        
        // Se não existir, cria um novo
        if (!hintToast) {
            const toastHTML = `
                <div id="contextualHintToast" class="position-fixed bottom-0 start-0 p-3" style="z-index: 1060;">
                    <div class="toast bg-dark border-info" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="8000">
                        <div class="toast-header bg-dark text-light border-bottom border-info">
                            <i class="bi bi-info-circle me-2 text-info"></i>
                            <strong class="me-auto">Dica</strong>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Fechar"></button>
                        </div>
                        <div class="toast-body text-light" id="hintToastBody">
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', toastHTML);
            hintToast = document.getElementById('contextualHintToast');
        }
        
        // Atualiza o texto da dica
        document.getElementById('hintToastBody').textContent = hintText;
        
        // Mostra a dica usando o Bootstrap Toast
        const toastElement = hintToast.querySelector('.toast');
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }
    
    // Iniciar com uma dica inicial depois de 3 segundos
    setTimeout(() => {
        // Usar a dica inicial do servidor, se disponível
        if (typeof initialHint === 'string' && initialHint) {
            showContextualHint(initialHint);
        } 
        // Caso contrário, gerar uma dica baseada na localização
        else if (gameState && gameState.currentLocation) {
            // Dica baseada na localização
            let hintText = "Use o comando 'olhar ao redor' para examinar seu ambiente.";
            
            if (gameState.currentLocation.includes('forest')) {
                hintText = "As florestas podem esconder muitos segredos. Experimente 'examinar árvores' ou 'procurar trilhas'.";
            } else if (gameState.currentLocation.includes('village')) {
                hintText = "Em vilas, você pode 'falar com aldeões' ou visitar edifícios como a 'taverna' ou o 'mercado'.";
            } else if (gameState.currentLocation.includes('cave')) {
                hintText = "Cavernas são perigosas. Use 'acender tocha' para enxergar melhor ou 'ouvir sons' para detectar criaturas.";
            }
            
            showContextualHint(hintText);
        }
    }, 3000);
    
    // Função para reproduzir áudio de introdução do personagem
    if (playIntroButton) {
        playIntroButton.addEventListener('click', function() {
            const audioId = this.getAttribute('data-audio-id');
            if (!audioId) return;
            
            // Alterar o botão para indicar carregamento
            playIntroButton.innerHTML = '<i class="bi bi-hourglass-split"></i>';
            playIntroButton.disabled = true;
            
            // Buscar os dados de áudio do servidor
            fetch(`/character_audio/${audioId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Erro ao buscar áudio');
                    }
                    return response.json();
                })
                .then(data => {
                    // Converter dados de áudio base64 para blob
                    const audioData = data.audio_data;
                    const audioText = data.audio_text;
                    
                    // Criar URL do blob para o áudio
                    const audioBlob = base64ToBlob(audioData, 'audio/mpeg');
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Configurar o player de áudio
                    audioIntroPlayer.src = audioUrl;
                    audioIntroText.textContent = audioText;
                    
                    // Mostrar o container de áudio
                    audioIntroContainer.classList.remove('d-none');
                    audioIntroContainer.classList.add('fade-in');
                    
                    // Reproduzir o áudio automaticamente
                    audioIntroPlayer.play();
                    
                    // Restaurar o botão
                    playIntroButton.innerHTML = '<i class="bi bi-volume-up"></i>';
                    playIntroButton.disabled = false;
                })
                .catch(error => {
                    console.error('Erro:', error);
                    // Restaurar o botão em caso de erro
                    playIntroButton.innerHTML = '<i class="bi bi-volume-up"></i>';
                    playIntroButton.disabled = false;
                    alert('Erro ao carregar o áudio de introdução.');
                });
        });
    }
    
    // Função para converter base64 para blob
    function base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteArrays = [];
        
        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);
            
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }
        
        return new Blob(byteArrays, {type: mimeType});
    }
});
