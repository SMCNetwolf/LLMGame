import os
import json 
import logging
import base64
from dotenv import dotenv_values
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



env_vars = dotenv_values('.env') 
os.environ['OPENAI_API_KEY'] = env_vars['OPENAI_API_KEY'] 
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") 




client = OpenAI(api_key=OPENAI_API_KEY) 



def generate_text_response(prompt):
    """ 
    Generate a text response using OpenAI's GPT model in Portuguese.
    
    Args:
        prompt (str): The prompt to send to the OpenAI API
        
    Returns:
        str: The generated text response in Portuguese
    """
    try: 
        # Using gpt-3.5-turbo which is more widely available
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "Você é um mestre de RPG. Forneça respostas sucintas, em português."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating text: {e}") 
        return "A magia antiga que alimenta este reino parece estar temporariamente enfraquecida. (Erro ao comunicar com o serviço de IA)"

def generate_image(prompt):
    """ 
    Generate an image using OpenAI's DALL-E model.
    
    Args:
        prompt (str): The prompt to send to the OpenAI API
        
    Returns: 
        str: The URL of the generated image
    """
    try:
        from filtering_toxicity import filter_image_prompt 
        
        
        is_appropriate, safe_prompt = filter_image_prompt(prompt) 
        
        if not is_appropriate:
            logger.warning(f"Image prompt was flagged as inappropriate: {prompt}")
            return create_placeholder_image() 
            
        logger.info(f"Safe image prompt: {safe_prompt}")
        
        response = client.images.generate(
            model="dall-e-2", 
            prompt=safe_prompt,
            n=1,
            size="512x512", 
        )
        return response.data[0].url
    except Exception as e:
        logger.error(f"Error generating image: {e}") 
        # Return a placeholder SVG image
        return create_placeholder_image()

def create_placeholder_image():
    """Create a placeholder SVG when image generation fails."""
    # Return the path to the static placeholder image
    return "/static/placeholder.svg"
    
def generate_audio(text, voice_type="onyx"):
    """
    Generate an audio file using OpenAI's TTS API.
    
    Args:
        text (str): The text to convert to speech
        voice_type (str): The voice type to use (alloy, echo, fable, onyx, nova, shimmer)
        
    Returns:
        str: Base64 encoded audio data or None if an error occurs
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_type,
            input=text
        )
        
        
        audio_data = response.content
        base64_audio = base64.b64encode(audio_data).decode('utf-8') 
        return base64_audio
    except Exception as e: 
        logger.error(f"Error generating audio: {e}")
        return None

def generate_character_introduction_audio(character_name, character_class, voice_type="onyx"):
    """
    Generate a personalized character introduction audio.
    
    Args:
        character_name (str): The character's name
        character_class (str): The character's class
        voice_type (str): The voice type to use
        
    Returns:
        tuple: (intro_text, base64_audio) or (None, None) if an error occurs
    """
    try:
        
        intro_text = generate_text_response(
            f"Crie uma introdução curta e dramática com cerca de 3 frases para {character_name}, um(a) {character_class} em \
                uma aventura de RPG. Fale na primeira pessoa, como se fosse o próprio personagem se apresentando. \
                Use linguagem épica e inspiradora. Mantenha a resposta com menos de 50 palavras."
        )
        
        
        audio_data = generate_audio(intro_text, voice_type) 
        return audio_data 
    except Exception as e:
        logger.error(f"Error generating character introduction audio: {e}")
        return None 

def parse_game_action(action_text):
    """
    Parse complex player actions in Portuguese into structured game actions.
    
    Args:
        action_text (str): The player's raw action text in Portuguese
        
    Returns:
        dict: Structured action data
    """
    try:
        
        response = client.chat.completions.create(
            model="o3-mini", 
            messages=[
                {"role": "system", "content": "Você é uma IA que analisa comandos de jogadores em um jogo de RPG. Extraia o tipo de ação e detalhes relevantes da entrada do jogador. Responda com um objeto JSON."},
                {"role": "user", "content": f"Analise esta ação do jogador em um formato estruturado: '{action_text}'. Responda com um objeto JSON válido tendo os campos action_type, target e details."}
            ],
            temperature=0.3
        )
        
        try: 
            return json.loads(response.choices[0].message.content) 
        except json.JSONDecodeError: 
            
            return { 
                "action_type": "text", 
                "target": None, 
                "details": {"raw_text": action_text} 
            } 
    except Exception as e:
        logger.error(f"Error parsing action: {e}")
        return {"action_type": "unknown", "target": None, "details": {}} 


