"""
Filtering and Toxicity Module for the Fantasy RPG

This module provides functions to filter inappropriate content
and ensure the game maintains appropriate standards.
"""

import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Content policy
CONTENT_POLICY = {
    "prohibited_themes": [
        "conteúdo sexual explícito",
        "violência gráfica excessiva",
        "discriminação racial",
        "discurso de ódio",
        "abuso infantil",
        "suicídio ou automutilação",
        "uso de drogas explícito",
        "atividades ilegais específicas",
        "informações pessoais identificáveis",
        "discurso político extremista",
        "bullying ou assédio",
        "conteúdo perturbador explícito"
    ],
    "age_rating": "12+",  # Suitable for ages 12 and up
    "violence_level": "moderado",  # Moderate fantasy violence allowed
    "language_level": "leve"  # Mild language allowed
}

# Placeholder for words/phrases that should be filtered
FILTERED_TERMS = {
    "high_severity": [
        # This would contain inappropriate words that should always be filtered
        # Empty for now as this is a template
    ],
    "medium_severity": [
        # This would contain questionable terms that should be filtered in most contexts
        # Empty for now as this is a template
    ],
    "low_severity": [
        # This would contain mild terms that might be allowed in certain contexts
        # Empty for now as this is a template
    ]
}

# Standard responses for rejected content
REJECTION_RESPONSES = {
    "general": "Sua solicitação não pode ser processada pois contém conteúdo inadequado para este jogo. \
        Por favor, tente novamente com uma abordagem diferente.",
    "violent": "Sua solicitação contém violência excessiva que vai além da temática do jogo. \
        Por favor, tente uma abordagem mais adequada para um jogo de fantasia medieval.",
    "offensive": "Seu comando contém linguagem ofensiva ou inapropriada. \
        Este jogo é destinado a ser uma experiência positiva e inclusiva para todos.",
    "out_of_context": "Sua solicitação se afasta demais do tema de fantasia medieval deste jogo. \
        Por favor, mantenha suas ações dentro do contexto do mundo do jogo."
}

def check_player_input(text):
    """
    Check player input for inappropriate content
    
    Args:
        text (str): The text to check
        
    Returns:
        tuple: (is_appropriate, rejection_message)
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check for high severity terms first
    for term in FILTERED_TERMS["high_severity"]:
        if term.lower() in text_lower:
            logger.warning(f"Player input contained high severity term: {term}")
            return False, REJECTION_RESPONSES["offensive"]
    
    # Check for medium severity terms
    for term in FILTERED_TERMS["medium_severity"]:
        if term.lower() in text_lower:
            logger.warning(f"Player input contained medium severity term: {term}")
            return False, REJECTION_RESPONSES["offensive"]
    
    # Check for low severity terms (might allow in certain contexts)
    low_severity_matches = []
    for term in FILTERED_TERMS["low_severity"]:
        if term.lower() in text_lower:
            low_severity_matches.append(term)
    
    # If there are many low severity terms, reject
    if len(low_severity_matches) >= 3:
        logger.warning(f"Player input contained multiple low severity terms: {low_severity_matches}")
        return False, REJECTION_RESPONSES["offensive"]
    
    # Check for excessive violence
    violence_indicators = ["matar", "assassinar", "torturar", "mutilar", "decapitar", "eviscerar"]
    violence_count = sum(1 for word in violence_indicators if word in text_lower)
    
    if violence_count >= 2:
        logger.warning(f"Player input contained excessive violence indicators")
        return False, REJECTION_RESPONSES["violent"]
    
    # Check for out-of-context requests
    out_of_context_indicators = ["internet", "telefone", "computador", "carro", "avião", "televisão", "arma de fogo"]
    out_of_context_count = sum(1 for word in out_of_context_indicators if word in text_lower)
    
    if out_of_context_count >= 1:
        logger.warning(f"Player input contained out-of-context indicators")
        return False, REJECTION_RESPONSES["out_of_context"]
    
    # If all checks pass, the content is appropriate
    return True, None

def check_ai_response(text):
    """
    Check AI response for inappropriate content
    
    Args:
        text (str): The text to check
        
    Returns:
        tuple: (is_appropriate, replacement_text)
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check for high severity terms first
    high_severity_found = False
    for term in FILTERED_TERMS["high_severity"]:
        if term.lower() in text_lower:
            high_severity_found = True
            text = re.sub(re.escape(term), "[conteúdo removido]", text, flags=re.IGNORECASE)
    
    if high_severity_found:
        logger.warning(f"AI response contained high severity terms that were filtered")
        return False, "A resposta gerada continha conteúdo inadequado e foi substituída. O narrador descreve uma cena apropriada para o tema do jogo."
    
    # Check for medium severity terms
    medium_severity_found = False
    for term in FILTERED_TERMS["medium_severity"]:
        if term.lower() in text_lower:
            medium_severity_found = True
            text = re.sub(re.escape(term), "[conteúdo removido]", text, flags=re.IGNORECASE)
    
    if medium_severity_found:
        logger.warning(f"AI response contained medium severity terms that were filtered")
        # We'll still return the filtered text, but mark it as inappropriate
        return False, text
    
    # For low severity terms, just filter them but consider the response appropriate
    for term in FILTERED_TERMS["low_severity"]:
        if term.lower() in text_lower:
            text = re.sub(re.escape(term), "[termo suavizado]", text, flags=re.IGNORECASE)
    
    # Check for excessive violence
    violence_indicators = ["sangue jorrando", "entranha", "desmembramento", "tortura", "agonia excruciante"]
    for indicator in violence_indicators:
        if indicator in text_lower:
            text = re.sub(indicator, "[descrição de combate]", text, flags=re.IGNORECASE)
    
    # If all checks pass or issues were filtered, return the (possibly modified) text
    return True, text

def add_safety_prompt_prefix(prompt):
    """
    Add safety instructions to the beginning of a prompt
    
    Args:
        prompt (str): The original prompt
        
    Returns:
        str: The prompt with safety instructions
    """
    safety_prefix = (
        "Gere uma resposta que seja adequada para um jogo de RPG de fantasia medieval com classificação 12+. "
        "Evite conteúdo sexual, violência gráfica excessiva, linguagem obscena, e temas adultos explícitos. "
        "Mantenha o conteúdo apropriado para adolescentes com violência de fantasia moderada semelhante a um "
        "livro ou filme de aventura de classificação 12+. "
        "Responda como um narrador de RPG ao seguinte cenário: "
    )
    
    return safety_prefix + prompt

def add_safety_prompt_suffix(prompt):
    """
    Add safety instructions to the end of a prompt
    
    Args:
        prompt (str): The original prompt
        
    Returns:
        str: The prompt with safety instructions
    """
    safety_suffix = (
        "\n\nLembre-se de manter sua resposta adequada para um jogo de RPG com classificação 12+, "
        "evitando violência gráfica, conteúdo sexual, linguagem obscena ou temas adultos explícitos."
    )
    
    return prompt + safety_suffix

def create_safety_system_message():
    """
    Create a system message for safety instructions
    
    Returns:
        str: The system message with safety instructions
    """
    return (
        "Você é um narrador de jogos de RPG de fantasia medieval que cria conteúdo adequado para jogadores "
        "de 12 anos ou mais. Você deve seguir estas diretrizes estritamente:\n"
        "1. Evite completamente qualquer conteúdo sexual ou sugestivo\n"
        "2. Descreva apenas violência de fantasia moderada, nunca gráfica ou excessiva\n"
        "3. Evite linguagem obscena ou palavrões\n"
        "4. Não inclua temas adultos explícitos como uso de drogas, suicídio, ou abuso\n"
        "5. Mantenha um tom de aventura e fantasia adequado para adolescentes\n"
        "6. Foque em temas como heroísmo, amizade, superação de desafios e exploração\n"
        "7. Se receber pedidos inadequados, redirecione para ações apropriadas ao jogo\n\n"
        "Você deve ser criativo e envolvente, mas sempre dentro dessas diretrizes de segurança."
    )

def filter_image_prompt(prompt):
    """
    Filter an image generation prompt for safety
    
    Args:
        prompt (str): The original image prompt
        
    Returns:
        tuple: (is_appropriate, filtered_prompt)
    """
    # Convert to lowercase for case-insensitive matching
    prompt_lower = prompt.lower()
    
    # Remover termos de metaprompt que podem disparar filtros
    # Palavras como "tentando", "gere", "GPT" podem disparar filtros
    metaprompt_terms = ["tentando", "gpt", "gere ", "gerando", "openai", "dall-e"]
    for term in metaprompt_terms:
        if term in prompt_lower:
            prompt = re.sub(re.escape(term), "", prompt, flags=re.IGNORECASE)
            logger.info(f"Removed metaprompt term from image prompt: {term}")
    
    # Limitar tamanho para evitar problemas
    if len(prompt) > 200:
        prompt = prompt[:200]
        logger.info("Truncated long image prompt")
    
    # Check for inappropriate terms in all severity levels
    for term in FILTERED_TERMS["high_severity"] + FILTERED_TERMS["medium_severity"]:
        if term.lower() in prompt_lower:
            logger.warning(f"Image prompt contained inappropriate term: {term}")
            return False, "Cena de fantasia apropriada para o jogo"
    
    # Check for problematic image request patterns
    problematic_patterns = [
        r"nu[ad]ez",
        r"sem roup[ao]",
        r"pouca[s]? roup[ao]",
        r"reveladoras?",
        r"seminuas?",
        r"scantily",
        r"explicit[ao]",
        r"gore",
        r"sangrento",
        r"mutilação",
        r"decapitação",
        r"real[íi]stico demais"
    ]
    
    for pattern in problematic_patterns:
        if re.search(pattern, prompt_lower):
            logger.warning(f"Image prompt matched problematic pattern: {pattern}")
            return False, "Cena de fantasia apropriada para o jogo"
    
    # Add safety suffix to the prompt
    safe_prompt = "Cena de RPG medieval fantástico, estilo artístico de jogo: " + prompt
    
    # Limitar novamente para garantir
    if len(safe_prompt) > 200:
        safe_prompt = safe_prompt[:200]
    
    return True, safe_prompt

def update_filter_database(term, severity, add_or_remove="add"):
    """
    Update the filter database with a new term or remove an existing one
    
    Args:
        term (str): The term to add or remove
        severity (str): The severity level ('high', 'medium', 'low')
        add_or_remove (str): Whether to add or remove the term
        
    Returns:
        bool: True if successful, False otherwise
    """
    if severity not in ["high", "medium", "low"]:
        logger.error(f"Invalid severity level: {severity}")
        return False
    
    severity_key = f"{severity}_severity"
    
    if add_or_remove == "add":
        if term.lower() not in [t.lower() for t in FILTERED_TERMS[severity_key]]:
            FILTERED_TERMS[severity_key].append(term)
            logger.info(f"Added '{term}' to {severity} severity filter")
            return True
        else:
            logger.warning(f"Term '{term}' already exists in {severity} severity filter")
            return False
    
    elif add_or_remove == "remove":
        for i, existing_term in enumerate(FILTERED_TERMS[severity_key]):
            if term.lower() == existing_term.lower():
                FILTERED_TERMS[severity_key].pop(i)
                logger.info(f"Removed '{term}' from {severity} severity filter")
                return True
        
        logger.warning(f"Term '{term}' not found in {severity} severity filter")
        return False
    
    else:
        logger.error(f"Invalid operation: {add_or_remove}")
        return False

def safe_ai_request(prompt, original_function, *args, **kwargs):
    """
    Wrapper function to ensure AI requests are safe
    
    Args:
        prompt (str): The original prompt
        original_function: The AI function to call
        *args, **kwargs: Additional arguments for the original function
        
    Returns:
        The result of the AI function call with safety measures applied
    """
    # First check if the prompt itself is appropriate
    is_appropriate, rejection_message = check_player_input(prompt)
    if not is_appropriate:
        return rejection_message
    
    # Apply safety measures to the prompt
    safe_prompt = add_safety_prompt_prefix(prompt)
    safe_prompt = add_safety_prompt_suffix(safe_prompt)
    
    # Call the original AI function with the safe prompt
    result = original_function(safe_prompt, *args, **kwargs)
    
    # Check the AI response
    response_appropriate, filtered_response = check_ai_response(result)
    
    # Return either the original response or the filtered version
    if response_appropriate:
        return result
    else:
        return filtered_response