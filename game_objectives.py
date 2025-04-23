"""
Game Objectives Module for the Fantasy RPG

This module defines the objectives and quests that players can complete in the game.
Each quest has requirements, rewards, and narrative elements.
"""

import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Quest difficulty levels
DIFFICULTY_LEVELS = {
    "novice": {"exp_multiplier": 1.0, "gold_multiplier": 1.0},
    "easy": {"exp_multiplier": 1.5, "gold_multiplier": 1.5},
    "medium": {"exp_multiplier": 2.0, "gold_multiplier": 2.0},
    "hard": {"exp_multiplier": 3.0, "gold_multiplier": 3.0},
    "epic": {"exp_multiplier": 5.0, "gold_multiplier": 5.0}
}

# Quest types
QUEST_TYPES = [
    "exploration",  # Discover new locations
    "combat",       # Defeat enemies
    "collection",   # Gather items
    "delivery",     # Deliver items to NPCs
    "escort",       # Protect NPCs
    "puzzle",       # Solve puzzles/riddles
    "crafting",     # Create items
    "diplomacy"     # Negotiate with NPCs
]

# Main quest definitions
MAIN_QUESTS = [
    {
        "id": "mq001",
        "title": "O Chamado do Destino",
        "description": "Você foi escolhido pelos anciãos para investigar uma antiga profecia sobre a chegada de uma grande escuridão.",
        "objective": "Visite o Oráculo nas Montanhas do Norte e descubra mais sobre a profecia.",
        "type": "exploration",
        "difficulty": "easy",
        "requirements": {
            "level_min": 1,
            "items_required": []
        },
        "rewards": {
            "experience": 100,
            "gold": 50,
            "items": ["Pergaminho do Destino"]
        },
        "next_quest_id": "mq002",
        "location": "Meadowbrook",
        "npc_giver": "Ancião Thorne"
    },
    {
        "id": "mq002",
        "title": "Fragmentos da Visão",
        "description": "O Oráculo revela que você deve encontrar três fragmentos mágicos para evitar que a escuridão se espalhe pelo reino.",
        "objective": "Encontre o primeiro fragmento escondido nas Ruínas de Eldrath.",
        "type": "exploration",
        "difficulty": "medium",
        "requirements": {
            "level_min": 3,
            "items_required": ["Pergaminho do Destino"],
            "quests_completed": ["mq001"]
        },
        "rewards": {
            "experience": 200,
            "gold": 100,
            "items": ["Fragmento da Luz"]
        },
        "next_quest_id": "mq003",
        "location": "Montanhas do Norte",
        "npc_giver": "Oráculo Elara"
    }
]

# Side quest definitions
SIDE_QUESTS = [
    {
        "id": "sq001",
        "title": "O Lobo Solitário",
        "description": "Um lobo feroz tem aterrorizado os fazendeiros locais. \
            O prefeito oferece uma recompensa para quem resolver este problema.",
        "objective": "Encontre e derrote o lobo feroz, ou encontre uma maneira pacífica de resolver o conflito.",
        "type": "combat",
        "difficulty": "novice",
        "requirements": {
            "level_min": 1,
            "items_required": []
        },
        "rewards": {
            "experience": 50,
            "gold": 25,
            "items": ["Colar de Dentes de Lobo"]
        },
        "location": "Meadowbrook",
        "npc_giver": "Prefeito Galen"
    },
    {
        "id": "sq002",
        "title": "Hervas Medicinais",
        "description": "A curandeira da vila precisa de ervas raras que crescem na Floresta Negra \
            para preparar remédios para os doentes.",
        "objective": "Colete 5 flores de beladona na Floresta Negra.",
        "type": "collection",
        "difficulty": "easy",
        "requirements": {
            "level_min": 2,
            "items_required": []
        },
        "rewards": {
            "experience": 75,
            "gold": 30,
            "items": ["Poção de Cura"]
        },
        "location": "Meadowbrook",
        "npc_giver": "Curandeira Lydia"
    }
]

def get_quest_by_id(quest_id):
    """
    Get a quest by its ID
    
    Args:
        quest_id (str): The ID of the quest to retrieve
        
    Returns:
        dict: The quest data or None if not found
    """
    for quest in MAIN_QUESTS:
        if quest["id"] == quest_id:
            return quest
            
    for quest in SIDE_QUESTS:
        if quest["id"] == quest_id:
            return quest
            
    return None

def get_available_quests(character_level, completed_quests=None, current_location=None):
    """
    Get quests available to a character based on their level and completed quests
    
    Args:
        character_level (int): The character's current level
        completed_quests (list): List of quest IDs the character has completed
        current_location (str): The character's current location
        
    Returns:
        list: List of available quests
    """
    if completed_quests is None:
        completed_quests = []
        
    available_quests = []
    
    # Check main quests
    for quest in MAIN_QUESTS:
        # Check if the quest level requirement is met
        if quest["requirements"]["level_min"] <= character_level:
            # Check if the quest is not already completed
            if quest["id"] not in completed_quests:
                # Check if required items are available (would need inventory check in actual implementation)
                # Check if required previous quests are completed
                prereq_quests = quest["requirements"].get("quests_completed", [])
                if all(q in completed_quests for q in prereq_quests):
                    # Check location if specified
                    if current_location is None or quest["location"] == current_location:
                        available_quests.append(quest)
    
    # Check side quests (similar logic)
    for quest in SIDE_QUESTS:
        if quest["requirements"]["level_min"] <= character_level:
            if quest["id"] not in completed_quests:
                if current_location is None or quest["location"] == current_location:
                    available_quests.append(quest)
    
    return available_quests

def calculate_quest_rewards(quest_id, character_level=1):
    """
    Calculate the final rewards for a quest based on character level and other factors
    
    Args:
        quest_id (str): The ID of the quest
        character_level (int): The character's current level
        
    Returns:
        dict: The calculated rewards
    """
    quest = get_quest_by_id(quest_id)
    if not quest:
        return None
        
    # Get base rewards
    base_rewards = quest["rewards"]
    
    # Get difficulty multipliers
    difficulty = quest["difficulty"]
    multipliers = DIFFICULTY_LEVELS[difficulty]
    
    # Calculate final rewards with level scaling
    level_scaling = 1.0 + (character_level - 1) * 0.1  # 10% increase per level
    
    final_rewards = {
        "experience": int(base_rewards["experience"] * multipliers["exp_multiplier"] * level_scaling),
        "gold": int(base_rewards["gold"] * multipliers["gold_multiplier"] * level_scaling),
        "items": base_rewards["items"]
    }
    
    return final_rewards

def mark_quest_complete(character_id, quest_id, game_state):
    """
    Mark a quest as complete in a character's game state
    
    Args:
        character_id (int): The character's ID
        quest_id (str): The completed quest ID
        game_state (dict): The character's game state
        
    Returns:
        dict: Updated game state
    """
    if "quest_progress" not in game_state:
        game_state["quest_progress"] = {}
        
    if "completed_quests" not in game_state["quest_progress"]:
        game_state["quest_progress"]["completed_quests"] = []
        
    if quest_id not in game_state["quest_progress"]["completed_quests"]:
        game_state["quest_progress"]["completed_quests"].append(quest_id)
        
    # Check if this quest unlocks a new one
    quest = get_quest_by_id(quest_id)
    if quest and "next_quest_id" in quest:
        if "available_quests" not in game_state["quest_progress"]:
            game_state["quest_progress"]["available_quests"] = []
            
        next_quest_id = quest["next_quest_id"]
        if next_quest_id not in game_state["quest_progress"]["available_quests"]:
            game_state["quest_progress"]["available_quests"].append(next_quest_id)
            
    return game_state

def generate_quest_prompt(quest_id, character_name):
    """
    Generate a prompt for the AI to create quest dialogue
    
    Args:
        quest_id (str): The ID of the quest
        character_name (str): The character's name
        
    Returns:
        str: The AI prompt for quest dialogue
    """
    quest = get_quest_by_id(quest_id)
    if not quest:
        return "Nenhuma missão encontrada."
        
    prompt = f"Você é {character_name}, um aventureiro em busca de glória. "
    prompt += f"Você encontrou {quest['npc_giver']} em {quest['location']}. "
    prompt += f"Eles têm uma missão para você: '{quest['title']}'. "
    prompt += f"Detalhes da missão: {quest['description']} "
    prompt += f"O que você precisa fazer: {quest['objective']}. "
    
    if quest.get("difficulty") in ["hard", "epic"]:
        prompt += "Esta parece ser uma missão muito perigosa. "
    
    prompt += "Crie um diálogo entre você e o NPC sobre esta missão."
    
    return prompt

def check_quest_completion(quest_id, action_data, game_state):
    """
    Check if a quest has been completed based on player actions
    
    Args:
        quest_id (str): The ID of the quest
        action_data (dict): Data about the player's action
        game_state (dict): The current game state
        
    Returns:
        bool: True if the quest is completed, False otherwise
    """
    quest = get_quest_by_id(quest_id)
    if not quest:
        return False
        
    # This would need to be expanded with more complex logic depending on the quest type
    if quest["type"] == "exploration":
        # Check if the player has reached the required location
        if action_data.get("action_type") == "move" and action_data.get("target") == quest.get("objective_location"):
            return True
            
    elif quest["type"] == "combat":
        # Check if the player has defeated the required enemy
        if action_data.get("action_type") == "attack" and action_data.get("target") == quest.get("objective_target"):
            return True
            
    elif quest["type"] == "collection":
        # Check if the player has collected the required items
        if "inventory" in game_state:
            inventory = json.loads(game_state["inventory"])
            required_items = quest.get("objective_items", [])
            
            # Check if all required items are in inventory with sufficient quantities
            all_items_collected = True
            for item_req in required_items:
                item_name = item_req["name"]
                item_count = item_req.get("count", 1)
                
                if item_name not in inventory or inventory[item_name] < item_count:
                    all_items_collected = False
                    break
                    
            return all_items_collected
    
    # Default to not completed
    return False