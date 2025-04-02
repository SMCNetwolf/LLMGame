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
    Generate a text response using OpenAI's GPT-4o model.
    
    Args:
        prompt (str): The prompt to send to the OpenAI API
        
    Returns:
        str: The generated text response
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an advanced fantasy RPG game master. Provide immersive, detailed responses that enhance the player's experience."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return "The ancient magic that powers this realm seems to be temporarily weakened. (Error communicating with AI service)"

def generate_image(prompt):
    """
    Generate an image using OpenAI's DALL-E model.
    
    Args:
        prompt (str): The prompt to send to the OpenAI API
        
    Returns:
        str: The URL of the generated image
    """
    try:
        enhanced_prompt = f"{prompt} Fantasy style, detailed, atmospheric lighting, 4K, high quality."
        response = client.images.generate(
            model="dall-e-3",
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
        Image generation failed
      </text>
      <text x="512" y="540" font-family="Arial" font-size="30" text-anchor="middle" fill="#ecf0f1">
        Please try again later
      </text>
    </svg>
    """
    return f"data:image/svg+xml;base64,{svg.encode('utf-8').hex()}"

def parse_game_action(action_text):
    """
    Parse complex player actions into structured game actions.
    
    Args:
        action_text (str): The player's raw action text
        
    Returns:
        dict: Structured action data
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI that parses player commands in an RPG game. Extract the action type and relevant details from the player's input. Respond with a JSON object."},
                {"role": "user", "content": f"Parse this player action into a structured format: '{action_text}'"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error parsing action: {e}")
        return {"action_type": "unknown", "target": None, "details": {}}
