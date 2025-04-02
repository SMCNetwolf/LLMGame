document.addEventListener('DOMContentLoaded', function() {
    const commandForm = document.getElementById('commandForm');
    const commandInput = document.getElementById('commandInput');
    const gameText = document.getElementById('gameText');
    const gameImage = document.getElementById('gameImage');
    const loadingOverlay = document.querySelector('.image-loading-overlay');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    
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
            
            // Add the response to history (this would normally happen server-side)
            // In a real implementation, the server would update the history
            // We would load the new state on the next request
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
});
