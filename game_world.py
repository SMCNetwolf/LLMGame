"""
Game World Module for the Fantasy RPG

This module defines the game world, including locations, NPCs, and the rules
of the game. It provides a structured world that can be easily modified
to create different versions of the game.
"""

import json
import logging
import random
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# World configuration
WORLD_CONFIG = {
    "name": "Terras de Eldoria",
    "description": "Um reino de fantasia medieval com diversas regiões, desde vilas pacíficas \
        até florestas sombrias e montanhas misteriosas.",
    "starting_location": "Meadowbrook"
}

# Character classes
CHARACTER_CLASSES = {
    "warrior": {
        "name": "Guerreiro",
        "description": "Especialistas em combate corpo a corpo e resistência física.",
        "base_stats": {
            "health": 120,
            "mana": 50,
            "strength": 8,
            "intelligence": 3,
            "dexterity": 5
        },
        "abilities": ["Golpe Poderoso", "Defesa Firme"],
        "starting_equipment": ["espada_simples", "armadura_couro"],
        "starting_inventory": ["pocao_cura_menor", "pocao_cura_menor"]
    },
    "mage": {
        "name": "Mago",
        "description": "Mestres da magia arcana e conhecimento.",
        "base_stats": {
            "health": 70,
            "mana": 120,
            "strength": 3,
            "intelligence": 10,
            "dexterity": 4
        },
        "abilities": ["Bola de Fogo", "Escudo Arcano"],
        "starting_equipment": ["cajado_aprendiz", "robe_mago"],
        "starting_inventory": ["pocao_mana_menor", "pocao_mana_menor"]
    },
    "ranger": {
        "name": "Caçador",
        "description": "Especialistas em combate à distância e sobrevivência na natureza.",
        "base_stats": {
            "health": 90,
            "mana": 70,
            "strength": 5,
            "intelligence": 5,
            "dexterity": 8
        },
        "abilities": ["Tiro Certeiro", "Rastreamento"],
        "starting_equipment": ["arco_curto", "armadura_couro"],
        "starting_inventory": ["pocao_cura_menor", "pocao_mana_menor"]
    }
}

# Game locations
LOCATIONS = {
    "Meadowbrook": {
        "name": "Meadowbrook",
        "description": "Uma vila pacífica com casas de telhado de palha e moradores amigáveis. \
            Cercada por campos verdejantes e próxima a um riacho cristalino.",
        "type": "village",
        "connections": ["Floresta Sombria", "Estrada do Comércio", "Colinas do Norte"],
        "npcs": ["mestre_vila", "comerciante", "ferreiro", "curandeira"],
        "services": ["inn", "shop", "blacksmith", "healer"],
        "quests": ["sq001", "sq002"],
        "danger_level": 1,
        "image_description": "Uma vila pacífica com casas de telhado de palha e moradores amigáveis."
    },
    "Floresta Sombria": {
        "name": "Floresta Sombria",
        "description": "Uma densa floresta onde a luz do sol mal penetra através da cobertura das árvores. \
            Ruídos estranhos podem ser ouvidos entre as sombras.",
        "type": "wilderness",
        "connections": ["Meadowbrook", "Ruínas de Eldrath", "Pântano Nebuloso"],
        "npcs": ["druida_eremita"],
        "enemies": ["lobo", "bandido", "aranha_gigante"],
        "quests": [],
        "danger_level": 3,
        "image_description": "Uma densa floresta onde a luz do sol mal penetra através da cobertura das árvores. Sombrio e misterioso."
    },
    "Estrada do Comércio": {
        "name": "Estrada do Comércio",
        "description": "Uma estrada bem percorrida que conecta várias aldeias e cidades. Mercadores e viajantes são vistos frequentemente.",
        "type": "road",
        "connections": ["Meadowbrook", "Portus", "Encruzilhada"],
        "npcs": ["mercador_ambulante", "guarda_estrada"],
        "enemies": ["bandido", "lobo"],
        "quests": [],
        "danger_level": 2,
        "image_description": "Uma estrada bem percorrida com mercadores e viajantes. Campos abertos."
    },
    "Portus": {
        "name": "Portus",
        "description": "Uma cidade portuária movimentada com navios de todos os cantos do mundo. \
            O ar tem cheiro de sal e aventura.",
        "type": "city",
        "connections": ["Estrada do Comércio", "Costa Tempestuosa"],
        "npcs": ["mestre_guilda", "capitao_navio", "mercador_exotico"],
        "services": ["inn", "shop", "guild", "dock"],
        "quests": [],
        "danger_level": 1,
        "image_description": "Uma cidade portuária movimentada com navios, docas e mercados. Pessoas de várias culturas."
    },
    "Colinas do Norte": {
        "name": "Colinas do Norte",
        "description": "Colinas verdejantes que ficam cada vez mais íngremes conforme se aproximam das montanhas. \
            Pastores e fazendeiros vivem em pequenas propriedades.",
        "type": "wilderness",
        "connections": ["Meadowbrook", "Montanhas do Norte", "Prados do Leste"],
        "npcs": ["pastor", "minerador"],
        "enemies": ["lobo", "urso"],
        "quests": [],
        "danger_level": 2,
        "image_description": "Colinas verdejantes com algumas fazendas espalhadas. Montanhas são visíveis ao fundo."
    },
    "Montanhas do Norte": {
        "name": "Montanhas do Norte",
        "description": "Altas montanhas cobertas de neve, com passagens estreitas e perigosas. \
            Dizem que criaturas antigas vivem nas cavernas profundas.",
        "type": "mountains",
        "connections": ["Colinas do Norte", "Vale do Oráculo"],
        "npcs": ["guia_montanha"],
        "enemies": ["troll_montanha", "urso", "lobo_da_neve"],
        "quests": [],
        "danger_level": 4,
        "image_description": "Altas montanhas cobertas de neve, com passagens estreitas. Terreno perigoso e clima severo."
    },
    "Vale do Oráculo": {
        "name": "Vale do Oráculo",
        "description": "Um vale misterioso entre as montanhas, onde névoa paira constantemente. \
            No centro está o Templo do Oráculo.",
        "type": "special",
        "connections": ["Montanhas do Norte"],
        "npcs": ["oraculo", "guardiao_templo"],
        "services": ["oracle"],
        "quests": ["mq001"],
        "danger_level": 2,
        "image_description": "Um vale misterioso com névoa constante. Um templo antigo no centro."
    },
    "Ruínas de Eldrath": {
        "name": "Ruínas de Eldrath",
        "description": "Ruínas de uma antiga civilização, agora cobertas de vegetação e habitadas por criaturas perigosas. \
            Artefatos valiosos podem estar escondidos aqui.",
        "type": "ruins",
        "connections": ["Floresta Sombria"],
        "enemies": ["esqueleto", "cultista", "construto_antigo"],
        "quests": ["mq002"],
        "danger_level": 5,
        "image_description": "Ruínas de uma antiga civilização, com colunas caídas e estruturas de pedra cobertas de vegetação."
    }
}

# NPCs
NPCS = {
    "mestre_vila": {
        "name": "Ancião Thorne",
        "description": "Um homem idoso com barba branca e olhos sábios. É o líder respeitado de Meadowbrook e \
            conhece muitas histórias antigas.",
        "role": "leader",
        "location": "Meadowbrook",
        "quests": ["mq001"],
        "dialogue": {
            "greeting": "Bem-vindo, viajante. Meadowbrook é um lugar pacífico, mas temo que tempos difíceis se aproximam.",
            "farewell": "Que os deuses guiem seus passos, aventureiro.",
            "quest_offer": "Tenho algo importante a pedir a alguém de coragem..."
        }
    },
    "comerciante": {
        "name": "Elias",
        "description": "Um homem rechonchudo com um sorriso amigável. Vende de tudo um pouco em sua loja bem abastecida.",
        "role": "merchant",
        "location": "Meadowbrook",
        "services": ["buy", "sell"],
        "inventory": ["pocao_cura_menor", "pocao_mana_menor", "corda", "tocha", "comida"],
        "dialogue": {
            "greeting": "Bem-vindo à minha humilde loja! Tenho tudo que um aventureiro precisa.",
            "farewell": "Volte sempre! Meus preços são os melhores da região.",
            "transaction": "É um prazer fazer negócios com você."
        }
    },
    "ferreiro": {
        "name": "Gorric",
        "description": "Um homem musculoso com braços fortes de anos trabalhando na forja. Sua barba tem marcas de queimaduras.",
        "role": "blacksmith",
        "location": "Meadowbrook",
        "services": ["repair", "craft", "buy", "sell"],
        "inventory": ["espada_simples", "armadura_couro", "adaga", "escudo"],
        "dialogue": {
            "greeting": "Precisa de uma lâmina afiada ou uma armadura resistente?",
            "farewell": "Que suas armas sempre estejam afiadas, amigo.",
            "transaction": "Uma peça de qualidade. Use-a bem."
        }
    },
    "curandeira": {
        "name": "Lydia",
        "description": "Uma mulher de meia-idade com cabelos grisalhos e um semblante sereno. \
            Conhece muitos remédios herbais.",
        "role": "healer",
        "location": "Meadowbrook",
        "services": ["heal", "buy", "sell"],
        "inventory": ["pocao_cura_menor", "erva_cura", "antidoto", "bandagem"],
        "quests": ["sq002"],
        "dialogue": {
            "greeting": "Que os espíritos da natureza o abençoem. Precisa de cura?",
            "farewell": "Que a saúde e a paz o acompanhem.",
            "quest_offer": "As pessoas da aldeia precisam de ervas medicinais, mas a Floresta Sombria é perigosa..."
        }
    },
    "oraculo": {
        "name": "Oráculo Elara",
        "description": "Uma figura enigmática coberta por um manto azul cintilante. Seus olhos parecem enxergar além do presente.",
        "role": "special",
        "location": "Vale do Oráculo",
        "quests": ["mq001", "mq002"],
        "dialogue": {
            "greeting": "Eu o esperava, viajante dos caminhos do destino.",
            "farewell": "Nossa reunião foi predita. E nos encontraremos novamente, quando as estrelas se alinharem.",
            "quest_offer": "A escuridão se aproxima. Três fragmentos devem ser encontrados para deter a maré crescente..."
        }
    }
}

# Enemies
ENEMIES = {
    "lobo": {
        "name": "Lobo Selvagem",
        "description": "Um lobo cinzento com olhos amarelos ferozes. Caça em alcateias e é territorial.",
        "type": "beast",
        "level": 1,
        "stats": {
            "health": 30,
            "attack": 5,
            "defense": 2,
            "xp_reward": 20,
            "gold_reward": [1, 5]
        },
        "loot_table": [
            {"item": "pele_lobo", "chance": 0.7},
            {"item": "carne_crua", "chance": 0.5}
        ],
        "locations": ["Floresta Sombria", "Estrada do Comércio", "Colinas do Norte"]
    },
    "bandido": {
        "name": "Bandido da Estrada",
        "description": "Um homem maltrapilho armado com uma adaga. Ataca viajantes para roubar seus pertences.",
        "type": "humanoid",
        "level": 2,
        "stats": {
            "health": 40,
            "attack": 6,
            "defense": 3,
            "xp_reward": 30,
            "gold_reward": [5, 15]
        },
        "loot_table": [
            {"item": "adaga", "chance": 0.3},
            {"item": "pocao_cura_menor", "chance": 0.2},
            {"item": "corda", "chance": 0.4}
        ],
        "locations": ["Floresta Sombria", "Estrada do Comércio"]
    },
    "esqueleto": {
        "name": "Esqueleto Antigo",
        "description": "Restos reanimados de um guerreiro há muito falecido. Seus ossos são mantidos unidos por magia negra.",
        "type": "undead",
        "level": 3,
        "stats": {
            "health": 35,
            "attack": 7,
            "defense": 4,
            "xp_reward": 40,
            "gold_reward": [0, 5]
        },
        "loot_table": [
            {"item": "espada_enferrujada", "chance": 0.4},
            {"item": "osso", "chance": 0.8},
            {"item": "amuleto_antigo", "chance": 0.1}
        ],
        "locations": ["Ruínas de Eldrath"]
    }
}

# Game rules and mechanics
GAME_RULES = {
    "leveling": {
        "base_xp_required": 100,  # Base XP for level 2
        "xp_scaling": 1.5,        # Multiplier for each level
        "stat_increase": {
            "health": 10,
            "mana": 8,
            "base_stats": 1       # Points to distribute among strength, intelligence, dexterity
        }
    },
    "combat": {
        "hit_chance_formula": "attacker_dexterity * 3 + level * 5",
        "damage_formula": {
            "physical": "weapon_damage + strength * 0.5",
            "magical": "spell_power + intelligence * 0.7"
        },
        "defense_formula": "armor_defense + dexterity * 0.3",
        "critical_hit": {
            "chance": "dexterity * 0.5",
            "multiplier": 1.5
        }
    },
    "rest": {
        "health_recovery": 0.5,   # 50% of max health
        "mana_recovery": 0.7      # 70% of max mana
    },
    "time": {
        "day_length": 24,         # Game hours
        "starting_hour": 8,
        "night_danger_increase": 1.5  # Danger level multiplier at night
    }
}

# World generation functions
def initialize_game_world():
    """
    Initialize the game world
    
    Returns:
        dict: A dictionary with the game world state
    """
    return {
        "world_name": WORLD_CONFIG["name"],
        "current_time": {
            "hour": GAME_RULES["time"]["starting_hour"],
            "day": 1
        },
        "discovered_locations": [WORLD_CONFIG["starting_location"]]
    }

def get_location_description(location_id, time_of_day=None):
    """
    Get a description of a location, optionally modified by time of day
    
    Args:
        location_id (str): The ID of the location
        time_of_day (str, optional): 'morning', 'afternoon', 'evening', or 'night'
        
    Returns:
        str: A description of the location
    """
    if location_id not in LOCATIONS:
        return "Este lugar não existe no mundo conhecido."
    
    location = LOCATIONS[location_id]
    description = location["description"]
    
    # Modify description based on time of day
    if time_of_day:
        if time_of_day == "morning":
            description += " A luz dourada da manhã ilumina o local."
        elif time_of_day == "afternoon":
            description += " O sol do meio-dia brilha intensamente."
        elif time_of_day == "evening":
            description += " A luz alaranjada do pôr do sol cria sombras longas."
        elif time_of_day == "night":
            description += " A escuridão da noite envolve tudo, iluminada apenas por estrelas e ocasionais lanternas."
    
    # Add information about connections
    connections = location["connections"]
    if connections:
        description += f" Daqui você pode seguir para: {', '.join(connections)}."
    
    # Add information about NPCs present
    if "npcs" in location and location["npcs"]:
        npc_names = [NPCS[npc_id]["name"] for npc_id in location["npcs"] if npc_id in NPCS]
        if npc_names:
            description += f" Você pode ver: {', '.join(npc_names)}."
    
    # Add information about services
    if "services" in location and location["services"]:
        service_types = {
            "inn": "uma estalagem",
            "shop": "uma loja",
            "blacksmith": "uma ferraria",
            "healer": "um curandeiro",
            "guild": "um salão de guilda",
            "dock": "um porto",
            "oracle": "um oráculo"
        }
        services = [service_types[s] for s in location["services"] if s in service_types]
        if services:
            description += f" Aqui você encontra: {', '.join(services)}."
    
    return description

def get_location_image_prompt(location_id, time_of_day=None, character=None):
    """
    Generate an image prompt for a location
    
    Args:
        location_id (str): The ID of the location
        time_of_day (str, optional): 'morning', 'afternoon', 'evening', or 'night'
        character (dict, optional): Character data to include in the image
        
    Returns:
        str: A prompt for image generation
    """
    if location_id not in LOCATIONS:
        return "Um lugar misterioso e desconhecido."
    
    location = LOCATIONS[location_id]
    prompt = location["image_description"]
    
    # Add time of day
    if time_of_day:
        if time_of_day == "morning":
            prompt += " Iluminado pela luz dourada da manhã."
        elif time_of_day == "afternoon":
            prompt += " Sob o sol forte do meio-dia."
        elif time_of_day == "evening":
            prompt += " Banhado pela luz alaranjada do pôr do sol."
        elif time_of_day == "night":
            prompt += " Envolto pela escuridão da noite, iluminado por estrelas e ocasionais lanternas."
    
    # Add character if provided
    if character:
        prompt = f"{character['name']}, {CHARACTER_CLASSES[character['character_class']]['name']}, {prompt}"
    
    prompt += " Cena de jogo RPG, ambientação de fantasia."
    
    return prompt

def get_available_npcs(location_id):
    """
    Get NPCs available at a location
    
    Args:
        location_id (str): The ID of the location
        
    Returns:
        list: A list of NPC data dictionaries
    """
    if location_id not in LOCATIONS:
        return []
    
    location = LOCATIONS[location_id]
    if "npcs" not in location or not location["npcs"]:
        return []
    
    npcs = []
    for npc_id in location["npcs"]:
        if npc_id in NPCS:
            npcs.append(NPCS[npc_id])
    
    return npcs

def get_potential_enemies(location_id, time_of_day=None):# TODO: Add more dangerous enemies at night or increase their level
    """
    Get potential enemies at a location
    
    Args:
        location_id (str): The ID of the location
        time_of_day (str, optional): 'morning', 'afternoon', 'evening', or 'night'
        
    Returns:
        list: A list of enemy data dictionaries
    """
    if location_id not in LOCATIONS:
        return []
    
    location = LOCATIONS[location_id]
    if "enemies" not in location or not location["enemies"]:
        return []
    
    enemies = []
    for enemy_id in location["enemies"]:
        if enemy_id in ENEMIES:
            enemies.append(ENEMIES[enemy_id])
    
    #Adjust enemy chances based on time of day
    if time_of_day == "night":
        # Add more dangerous enemies at night or increase their level
        pass
    
    return enemies

def encounter_chance(location_id, time_of_day=None):
    """
    Calculate the chance of an enemy encounter at a location
    
    Args:
        location_id (str): The ID of the location
        time_of_day (str, optional): 'morning', 'afternoon', 'evening', or 'night'
        
    Returns:
        float: The chance of an encounter (0-1)
    """
    if location_id not in LOCATIONS:
        return 0
    
    location = LOCATIONS[location_id]
    base_chance = location["danger_level"] * 0.1  # 10% per danger level
    
    # Adjust for time of day
    if time_of_day == "night":
        base_chance *= GAME_RULES["time"]["night_danger_increase"]
    
    return min(base_chance, 0.9)  # Cap at 90%

def calculate_xp_for_level(level):
    """
    Calculate the XP required for a given level
    
    Args:
        level (int): The level to calculate XP for
        
    Returns:
        int: The amount of XP required
    """
    if level <= 1:
        return 0
    
    base_xp = GAME_RULES["leveling"]["base_xp_required"]
    scaling = GAME_RULES["leveling"]["xp_scaling"]
    
    return int(base_xp * (scaling ** (level - 2)))

def get_character_class_data(class_id):
    """
    Get data for a character class
    
    Args:
        class_id (str): The ID of the character class
        
    Returns:
        dict: The character class data or None if not found
    """
    return CHARACTER_CLASSES.get(class_id)

def generate_npc_dialogue(npc_id, dialogue_type, character=None):
    """
    Generate dialogue for an NPC
    
    Args:
        npc_id (str): The ID of the NPC
        dialogue_type (str): The type of dialogue ('greeting', 'farewell', 'quest_offer', etc.)
        character (dict, optional): Character data to personalize the dialogue
        
    Returns:
        str: The NPC dialogue
    """
    if npc_id not in NPCS:
        return "..."
    
    npc = NPCS[npc_id]
    if "dialogue" not in npc or dialogue_type not in npc["dialogue"]:
        return "..."
    
    dialogue = npc["dialogue"][dialogue_type]
    
    # Personalize dialogue if character data is provided
    if character:
        dialogue = dialogue.replace("{character_name}", character["name"])
        
        if "character_class" in character:
            class_name = CHARACTER_CLASSES[character["character_class"]]["name"]
            dialogue = dialogue.replace("{character_class}", class_name)
    
    return dialogue

def random_encounter(location_id, character_level, time_of_day=None):
    """
    Generate a random encounter for a location
    
    Args:
        location_id (str): The ID of the location
        character_level (int): The character's level
        time_of_day (str, optional): 'morning', 'afternoon', 'evening', or 'night'
        
    Returns:
        dict: Encounter data or None if no encounter
    """
    # Check if an encounter happens
    chance = encounter_chance(location_id, time_of_day)
    if random.random() > chance:
        return None
    
    # Get potential enemies
    potential_enemies = get_potential_enemies(location_id, time_of_day)
    if not potential_enemies:
        return None
    
    # Select an enemy
    enemy = random.choice(potential_enemies)
    
    # Adjust enemy level based on character level
    enemy_level = enemy["level"]
    if character_level > enemy_level + 2:
        # Scale up the enemy for higher level characters
        enemy_level = max(enemy_level, character_level - 2)
    
    # Create encounter data
    encounter = {
        "type": "combat",
        "enemy": enemy["name"],
        "enemy_description": enemy["description"],
        "enemy_level": enemy_level,
        "enemy_stats": {
            "health": enemy["stats"]["health"] + (enemy_level - enemy["level"]) * 10,
            "attack": enemy["stats"]["attack"] + (enemy_level - enemy["level"]) * 2,
            "defense": enemy["stats"]["defense"] + (enemy_level - enemy["level"])
        },
        "xp_reward": enemy["stats"]["xp_reward"] * (1 + 0.1 * (enemy_level - enemy["level"])),
        "gold_reward": random.randint(enemy["stats"]["gold_reward"][0], enemy["stats"]["gold_reward"][1])
    }
    
    # Add potential loot
    encounter["potential_loot"] = []
    for loot in enemy["loot_table"]:
        if random.random() <= loot["chance"]:
            encounter["potential_loot"].append(loot["item"])
    
    return encounter

def create_world_generation_prompt():
    """
    Create a prompt for generating a custom world
    
    Returns:
        str: A prompt for world generation
    """
    prompt = "Crie um mundo de fantasia para um jogo de RPG com as seguintes características:\n\n"
    prompt += "1. Nome do mundo\n"
    prompt += "2. Descrição geral do mundo e sua história\n"
    prompt += "3. 5-10 locais importantes (cidades, florestas, masmorras, etc.) com descrições detalhadas\n"
    prompt += "4. 5-10 NPCs importantes com nomes, descrições e papéis no mundo\n"
    prompt += "5. 3-5 facções ou reinos com suas motivações e relações entre si\n"
    prompt += "6. 3-5 ameaças principais que os jogadores podem enfrentar\n"
    prompt += "7. Alguns segredos ou mistérios que os jogadores podem descobrir\n\n"
    prompt += "Use um tema de fantasia medieval com elementos mágicos. Seja criativo e crie um mundo rico e imersivo."
    
    return prompt

def parse_custom_world_data(world_data_text):
    """
    Parse custom world data from text
    
    Args:
        world_data_text (str): The text with world data
        
    Returns:
        dict: Parsed world data
    """
    # In a real implementation, this would parse structured text into a world data dictionary
    # For now we'll return a placeholder
    return {
        "world_name": "Nome do Mundo Personalizado",
        "description": "Descrição do mundo personalizado...",
        "locations": {},
        "npcs": {},
        "factions": {},
        "threats": {},
        "secrets": []
    }

def save_custom_world(world_data, filename="custom_world.json"):
    """
    Save custom world data to a file
    
    Args:
        world_data (dict): The world data to save
        filename (str): The filename to save to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, "w") as f:
            json.dump(world_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving custom world: {e}")
        return False

def load_custom_world(filename="custom_world.json"):
    """
    Load custom world data from a file
    
    Args:
        filename (str): The filename to load from
        
    Returns:
        dict: The loaded world data or None if the file doesn't exist
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                world_data = json.load(f)
            return world_data
        else:
            return None
    except Exception as e:
        logger.error(f"Error loading custom world: {e}")
        return None