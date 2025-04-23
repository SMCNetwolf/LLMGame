/**
 * Gerenciador de áudio para o jogo RPG
 * Controla a reprodução de música de fundo baseada na localização do jogador
 */

class AudioManager {
    constructor() {
        this.backgroundMusic = null;
        this.currentLocation = null;
        this.audioVolume = 0.3; // Volume padrão (30%)
        this.isMuted = false;
        this.locationMusicMap = {
            // Mapeamento de localizações para músicas temáticas
            'village_of_meadowbrook': '/static/audio/peaceful_village.mp3',
            'forest_of_whispers': '/static/audio/mysterious_forest.mp3',
            'ancient_ruins': '/static/audio/dark_ruins.mp3',
            'mountain_pass': '/static/audio/epic_mountains.mp3',
            'tavern': '/static/audio/tavern_music.mp3',
            'castle': '/static/audio/royal_castle.mp3',
            'cave': '/static/audio/cave_ambience.mp3',
            'beach': '/static/audio/ocean_waves.mp3',
            'dark_forest': '/static/audio/dark_forest.mp3',
            // Música padrão para locais sem música específica
            'default': '/static/audio/adventure_theme.mp3'
        };
        
        // Inicializa o elemento de áudio
        this.initAudio();
    }
    
    /**
     * Inicializa o elemento de áudio e adiciona controles na interface
     */
    initAudio() {
        // Criar elemento de áudio se não existir
        if (!this.backgroundMusic) {
            this.backgroundMusic = new Audio();
            this.backgroundMusic.loop = true;
            this.backgroundMusic.volume = this.audioVolume;
            
            // Adicionar controles de música na interface
            this.createAudioControls();
        }
    }
    
    /**
     * Cria os controles de áudio na interface
     */
    createAudioControls() {
        // Criar div para controles de áudio no canto inferior direito
        const audioControlsHTML = `
            <div id="audioControls" class="position-fixed bottom-0 end-0 p-3 audio-controls">
                <div class="btn-group">
                    <button id="toggleMusicBtn" class="btn btn-sm btn-outline-secondary">
                        <i class="bi bi-volume-up"></i>
                    </button>
                    <button id="musicVolumeBtn" class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                        Volume
                    </button>
                    <div class="dropdown-menu p-2 dropdown-menu-end">
                        <input type="range" id="volumeSlider" class="form-range" min="0" max="100" value="30">
                    </div>
                </div>
            </div>
        `;
        
        // Inserir controles na página
        document.body.insertAdjacentHTML('beforeend', audioControlsHTML);
        
        // Configurar eventos
        document.getElementById('toggleMusicBtn').addEventListener('click', () => this.toggleMute());
        document.getElementById('volumeSlider').addEventListener('input', (e) => this.setVolume(e.target.value / 100));
    }
    
    /**
     * Alterna entre mudo e som
     */
    toggleMute() {
        this.isMuted = !this.isMuted;
        this.backgroundMusic.volume = this.isMuted ? 0 : this.audioVolume;
        
        // Atualizar ícone do botão
        const muteButton = document.getElementById('toggleMusicBtn');
        if (muteButton) {
            muteButton.innerHTML = this.isMuted ? 
                '<i class="bi bi-volume-mute"></i>' : 
                '<i class="bi bi-volume-up"></i>';
        }
    }
    
    /**
     * Define o volume da música
     * @param {number} volume - Volume (0 a 1)
     */
    setVolume(volume) {
        this.audioVolume = volume;
        if (!this.isMuted) {
            this.backgroundMusic.volume = volume;
        }
    }
    
    /**
     * Reproduz música baseada na localização
     * @param {string} location - ID da localização atual
     */
    playLocationMusic(location) {
        // Se a localização não mudou, não fazemos nada
        if (this.currentLocation === location) {
            return;
        }
        
        this.currentLocation = location;
        
        // Encontrar o caminho da música para a localização
        const musicPath = this.locationMusicMap[location] || this.locationMusicMap['default'];
        
        // Atualizar a fonte do áudio
        this.backgroundMusic.src = musicPath;
        
        // Exibir botão de reprodução de música para interação do usuário
        // (necessário para contornar restrições de autoplay do navegador)
        this.showPlayMusicNotification();
    }
    
    /**
     * Mostra uma notificação para o usuário iniciar a música manualmente
     * (contorna restrições de autoplay do navegador)
     */
    showPlayMusicNotification() {
        // Verificar primeiro se o arquivo de música existe
        const musicPath = this.backgroundMusic.src;
        
        // Teste prévio se o arquivo é acessível
        fetch(musicPath)
            .then(response => {
                if (!response.ok || response.headers.get('content-length') < 1000) {
                    // Arquivo não existe ou é muito pequeno (placeholder)
                    console.warn('Arquivos de música não disponíveis ou são placeholders');
                    return false;
                }
                return true;
            })
            .then(musicExists => {
                if (!musicExists) {
                    // Não exibir notificação se a música não existir
                    return;
                }
                
                // Remover notificação existente, se houver
                const existingNotification = document.getElementById('playMusicNotification');
                if (existingNotification) {
                    existingNotification.remove();
                }
                
                // Criar notificação para iniciar música
                const notificationHTML = `
                    <div id="playMusicNotification" class="position-fixed top-0 start-50 translate-middle-x p-3 mt-2" 
                        style="z-index: 1050; max-width: 300px;">
                        <div class="toast show bg-dark text-light" role="alert">
                            <div class="toast-header bg-dark text-light border-bottom border-secondary">
                                <i class="bi bi-music-note me-2"></i>
                                <strong class="me-auto">Música de Fundo</strong>
                                <button type="button" class="btn-close btn-close-white" 
                                    onclick="document.getElementById('playMusicNotification').remove()"></button>
                            </div>
                            <div class="toast-body">
                                <p class="small mb-2">Iniciar música temática para esta localização?</p>
                                <button id="startMusicBtn" class="btn btn-sm btn-outline-light w-100">
                                    <i class="bi bi-play-fill"></i> Tocar Música
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Inserir na página
                document.body.insertAdjacentHTML('beforeend', notificationHTML);
                
                // Configurar botão para iniciar a música
                document.getElementById('startMusicBtn').addEventListener('click', () => {
                    // Iniciar reprodução e remover notificação
                    this.backgroundMusic.play()
                        .then(() => {
                            // Sucesso!
                            document.getElementById('playMusicNotification').remove();
                        })
                        .catch(error => {
                            console.error('Falha ao reproduzir música:', error);
                            // Exibir mensagem de erro na notificação
                            const notificationBody = document.querySelector('#playMusicNotification .toast-body');
                            if (notificationBody) {
                                notificationBody.innerHTML = `
                                    <p class="small text-warning mb-2">Não foi possível iniciar a música. Verifique as configurações do seu navegador.</p>
                                    <button class="btn btn-sm btn-outline-light w-100" 
                                        onclick="document.getElementById('playMusicNotification').remove()">
                                        Fechar
                                    </button>
                                `;
                            }
                        });
                });
            })
            .catch(error => {
                console.error('Erro ao verificar arquivo de música:', error);
            });
    }
    
    /**
     * Faz uma transição suave entre músicas com fade out/in
     * @param {string} newMusicPath - Caminho para a nova música
     */
    fadeOutAndSwitch(newMusicPath) {
        const originalVolume = this.backgroundMusic.volume;
        let volume = originalVolume;
        
        // Efeito de fade out
        const fadeOut = setInterval(() => {
            volume -= 0.05;
            if (volume <= 0) {
                // Quando o volume chegar a zero, trocar a música
                clearInterval(fadeOut);
                this.backgroundMusic.pause();
                this.backgroundMusic.src = newMusicPath;
                this.backgroundMusic.volume = 0;
                
                // Iniciar a nova música e fazer fade in
                this.backgroundMusic.play().then(() => {
                    let newVolume = 0;
                    const fadeIn = setInterval(() => {
                        newVolume += 0.05;
                        if (newVolume >= originalVolume) {
                            clearInterval(fadeIn);
                            this.backgroundMusic.volume = originalVolume;
                        } else {
                            this.backgroundMusic.volume = newVolume;
                        }
                    }, 100);
                }).catch(error => {
                    console.warn('Não foi possível reproduzir música automaticamente:', error);
                });
            } else {
                this.backgroundMusic.volume = volume;
            }
        }, 100);
    }
}

// Inicializar o gerenciador de áudio quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    window.audioManager = new AudioManager();
    
    // Se já houver um estado de jogo carregado, iniciar a música apropriada
    if (typeof gameState !== 'undefined' && gameState.currentLocation) {
        window.audioManager.playLocationMusic(gameState.currentLocation);
    }
});