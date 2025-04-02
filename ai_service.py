import os
import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
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
                {"role": "system", "content": "Você é um mestre de RPG de fantasia avançado. Forneça respostas imersivas e detalhadas em português que enriqueçam a experiência do jogador. Use linguagem rica e descritiva para mundos de fantasia."},
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
        enhanced_prompt = f"{prompt} Fantasy style, detailed, atmospheric lighting, high quality."
        response = client.images.generate(
            model="dall-e-2",  # Using dall-e-2 which is more widely available
            prompt=enhanced_prompt,
            n=1,
            size="1024x1024",
        )
        return response.data[0].url
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        # Return a placeholder SVG image
        return create_placeholder_image()

def create_placeholder_image():
    """Create a placeholder SVG when image generation fails."""
    svg = """
    <svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
      <rect width="1024" height="1024" fill="#2c3e50"/>
      <text x="512" y="480" font-family="Arial" font-size="40" text-anchor="middle" fill="#ecf0f1">
        Falha na geração da imagem
      </text>
      <text x="512" y="540" font-family="Arial" font-size="30" text-anchor="middle" fill="#ecf0f1">
        Por favor, tente novamente mais tarde
      </text>
    </svg>
    """
    return f"data:image/svg+xml;base64,{svg.encode('utf-8').hex()}"

def parse_game_action(action_text):
    """
    Parse complex player actions in Portuguese into structured game actions.
    
    Args:
        action_text (str): The player's raw action text in Portuguese
        
    Returns:
        dict: Structured action data
    """
    try:
        # Using o3-mini as specified
        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "Você é uma IA que analisa comandos de jogadores em um jogo de RPG em português. Extraia o tipo de ação e detalhes relevantes da entrada do jogador. Responda com um objeto JSON."},
                {"role": "user", "content": f"Analise esta ação do jogador em um formato estruturado: '{action_text}'. Responda com um objeto JSON válido tendo os campos action_type, target e details."}
            ],
            temperature=0.3
        )
        # Try to parse as JSON, but handle potential non-JSON responses
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # If response isn't valid JSON, create a basic structure
            return {
                "action_type": "text",
                "target": None,
                "details": {"raw_text": action_text}
            }
    except Exception as e:
        logger.error(f"Error parsing action: {e}")
        return {"action_type": "unknown", "target": None, "details": {}}
