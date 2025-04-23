"""
Inventory System Module for the Fantasy RPG

This module manages the character's inventory, including items, 
equipment, and currency. It provides functions for adding, removing,
and using items.
"""

import json
import logging
import os
from ai_service import generate_text_response, generate_image

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Item categories
ITEM_CATEGORIES = {
    "weapon": "Arma",
    "armor": "Armadura",
    "potion": "Poção",
    "scroll": "Pergaminho",
    "key": "Chave",
    "quest": "Item de Missão",
    "material": "Material",
    "food": "Comida",
    "treasure": "Tesouro"
}

# Base items database
BASE_ITEMS = {
    # Weapons
    "espada_simples": {
        "name": "Espada Simples",
        "description": "Uma espada básica de ferro. Confiável, porém comum.",
        "category": "weapon",
        "value": 10,
        "weight": 3,
        "stats": {
            "damage": 5,
            "durability": 100
        },
        "requirements": {
            "level": 1,
            "strength": 3
        }
    },
    "arco_curto": {
        "name": "Arco Curto",
        "description": "Um arco pequeno feito de madeira flexível.",
        "category": "weapon",
        "value": 15,
        "weight": 2,
        "stats": {
            "damage": 4,
            "range": 20,
            "durability": 80
        },
        "requirements": {
            "level": 1,
            "dexterity": 4
        }
    },
    "cajado_aprendiz": {
        "name": "Cajado de Aprendiz",
        "description": "Um cajado básico que ajuda a canalizar magia.",
        "category": "weapon",
        "value": 20,
        "weight": 2,
        "stats": {
            "damage": 3,
            "magic_boost": 2,
            "durability": 90
        },
        "requirements": {
            "level": 1,
            "intelligence": 5
        }
    },
    
    # Armor
    "armadura_couro": {
        "name": "Armadura de Couro",
        "description": "Uma armadura básica feita de couro curtido.",
        "category": "armor",
        "value": 12,
        "weight": 4,
        "stats": {
            "defense": 3,
            "durability": 90
        },
        "requirements": {
            "level": 1
        }
    },
    "robe_mago": {
        "name": "Robe de Mago",
        "description": "Robe simples com símbolos arcanos bordados.",
        "category": "armor",
        "value": 14,
        "weight": 1,
        "stats": {
            "defense": 1,
            "magic_resistance": 3,
            "durability": 60
        },
        "requirements": {
            "level": 1,
            "intelligence": 4
        }
    },
    
    # Potions
    "pocao_cura_menor": {
        "name": "Poção de Cura Menor",
        "description": "Um frasco contendo um líquido vermelho que restaura um pouco de saúde.",
        "category": "potion",
        "value": 5,
        "weight": 0.5,
        "stats": {
            "health_restore": 20
        },
        "consumable": True
    },
    "pocao_mana_menor": {
        "name": "Poção de Mana Menor",
        "description": "Um frasco contendo um líquido azul que restaura um pouco de mana.",
        "category": "potion",
        "value": 5,
        "weight": 0.5,
        "stats": {
            "mana_restore": 20
        },
        "consumable": True
    },
    
    # Quest items
    "pergaminho_destino": {
        "name": "Pergaminho do Destino",
        "description": "Um antigo pergaminho com uma profecia sobre a escuridão vindoura.",
        "category": "quest",
        "value": 0,
        "weight": 0.1,
        "quest_id": "mq001"
    },
    "fragmento_luz": {
        "name": "Fragmento da Luz",
        "description": "Um cristal brilhante que parece conter energia pura.",
        "category": "quest",
        "value": 0,
        "weight": 0.2,
        "quest_id": "mq002"
    },
    
    # Materials
    "pele_lobo": {
        "name": "Pele de Lobo",
        "description": "Uma pele de lobo em bom estado, útil para artesanato.",
        "category": "material",
        "value": 3,
        "weight": 1
    },
    "erva_cura": {
        "name": "Erva de Cura",
        "description": "Uma planta com propriedades medicinais.",
        "category": "material",
        "value": 2,
        "weight": 0.1
    }
}

def initialize_inventory(character_id=None):
    """
    Initialize a new inventory for a character
    
    Args:
        character_id (int, optional): The character's ID
        
    Returns:
        dict: A new inventory dictionary
    """
    inventory = {
        "gold": 10,
        "capacity": {
            "max_weight": 50,
            "current_weight": 0
        },
        "equipped": {
            "weapon": None,
            "armor": None,
            "accessory": None
        },
        "items": {}
    }
    
    # Add starting items based on character class (would need to be expanded)
    if character_id:
        # In a real implementation, we would load character data and adjust starting items
        pass
    
    return inventory

def add_item(inventory, item_id, quantity=1):
    """
    Add an item to the inventory
    
    Args:
        inventory (dict): The inventory dictionary
        item_id (str): The ID of the item to add
        quantity (int): The quantity to add
        
    Returns:
        dict: The updated inventory
    """
    # Check if the item exists in the database
    if item_id not in BASE_ITEMS:
        logger.error(f"Item with ID {item_id} not found in the database")
        return inventory, False
    
    item = BASE_ITEMS[item_id]
    
    # Check weight limits
    total_new_weight = item["weight"] * quantity
    if inventory["capacity"]["current_weight"] + total_new_weight > inventory["capacity"]["max_weight"]:
        logger.info(f"Inventory is too full to add {quantity} {item['name']}")
        return inventory, False
    
    # Add the item to inventory
    if item_id in inventory["items"]:
        inventory["items"][item_id]["quantity"] += quantity
    else:
        inventory["items"][item_id] = {
            "quantity": quantity,
            "item_data": item
        }
    
    # Update inventory weight
    inventory["capacity"]["current_weight"] += total_new_weight
    
    logger.info(f"Added {quantity} {item['name']} to inventory")
    return inventory, True

def remove_item(inventory, item_id, quantity=1):
    """
    Remove an item from the inventory
    
    Args:
        inventory (dict): The inventory dictionary
        item_id (str): The ID of the item to remove
        quantity (int): The quantity to remove
        
    Returns:
        dict: The updated inventory
    """
    # Check if the item exists in the inventory
    if item_id not in inventory["items"]:
        logger.error(f"Item with ID {item_id} not found in inventory")
        return inventory, False
    
    # Check if there's enough quantity
    if inventory["items"][item_id]["quantity"] < quantity:
        logger.error(f"Not enough {BASE_ITEMS[item_id]['name']} in inventory")
        return inventory, False
    
    # Remove the item
    inventory["items"][item_id]["quantity"] -= quantity
    
    # Update inventory weight
    item_weight = BASE_ITEMS[item_id]["weight"] * quantity
    inventory["capacity"]["current_weight"] -= item_weight
    
    # Remove the item entirely if quantity is 0
    if inventory["items"][item_id]["quantity"] <= 0:
        del inventory["items"][item_id]
    
    logger.info(f"Removed {quantity} {BASE_ITEMS[item_id]['name']} from inventory")
    return inventory, True

def use_item(inventory, item_id, character_stats=None):
    """
    Use a consumable item from the inventory
    
    Args:
        inventory (dict): The inventory dictionary
        item_id (str): The ID of the item to use
        character_stats (dict, optional): The character's stats to modify
        
    Returns:
        tuple: (updated_inventory, updated_stats, result_message)
    """
    # Check if the item exists in the inventory
    if item_id not in inventory["items"]:
        return inventory, character_stats, "Item não encontrado no inventário."
    
    item = BASE_ITEMS[item_id]
    
    # Check if the item is consumable
    if not item.get("consumable", False):
        return inventory, character_stats, f"{item['name']} não é um item consumível."
    
    # Apply item effects to character stats
    result_message = f"Você usou {item['name']}. "
    
    if character_stats:
        if "health_restore" in item.get("stats", {}):
            restore_amount = item["stats"]["health_restore"]
            character_stats["health"] = min(character_stats["health"] + restore_amount, 100)  # Assuming max health is 100
            result_message += f"Recuperou {restore_amount} pontos de saúde."
            
        if "mana_restore" in item.get("stats", {}):
            restore_amount = item["stats"]["mana_restore"]
            character_stats["mana"] = min(character_stats["mana"] + restore_amount, 100)  # Assuming max mana is 100
            result_message += f"Recuperou {restore_amount} pontos de mana."
    
    # Remove the item from inventory (quantity 1)
    inventory, _ = remove_item(inventory, item_id, 1)
    
    return inventory, character_stats, result_message

def equip_item(inventory, item_id, character_stats=None):
    """
    Equip an item from the inventory
    
    Args:
        inventory (dict): The inventory dictionary
        item_id (str): The ID of the item to equip
        character_stats (dict, optional): The character's stats to modify
        
    Returns:
        tuple: (updated_inventory, updated_stats, result_message)
    """
    # Check if the item exists in the inventory
    if item_id not in inventory["items"]:
        return inventory, character_stats, "Item não encontrado no inventário."
    
    item = BASE_ITEMS[item_id]
    
    # Check if the item is equippable
    if item["category"] not in ["weapon", "armor", "accessory"]:
        return inventory, character_stats, f"{item['name']} não pode ser equipado."
    
    # Check requirements if character stats are provided
    if character_stats:
        requirements = item.get("requirements", {})
        
        if "level" in requirements and character_stats["level"] < requirements["level"]:
            return inventory, character_stats, f"Nível {requirements['level']} necessário para equipar {item['name']}."
            
        if "strength" in requirements and character_stats["strength"] < requirements["strength"]:
            return inventory, character_stats, f"Força {requirements['strength']} necessária para equipar {item['name']}."
            
        if "dexterity" in requirements and character_stats["dexterity"] < requirements["dexterity"]:
            return inventory, character_stats, f"Destreza {requirements['dexterity']} necessária para equipar {item['name']}."
            
        if "intelligence" in requirements and character_stats["intelligence"] < requirements["intelligence"]:
            return inventory, character_stats, f"Inteligência {requirements['intelligence']} necessária para equipar {item['name']}."
    
    # Unequip current item in the slot if any
    slot = item["category"]
    current_equipped = inventory["equipped"][slot]
    
    if current_equipped:
        # Add the currently equipped item back to inventory
        if current_equipped in inventory["items"]:
            inventory["items"][current_equipped]["quantity"] += 1
        else:
            inventory["items"][current_equipped] = {
                "quantity": 1,
                "item_data": BASE_ITEMS[current_equipped]
            }
    
    # Equip the new item
    inventory["equipped"][slot] = item_id
    
    # Remove the equipped item from inventory count
    inventory["items"][item_id]["quantity"] -= 1
    if inventory["items"][item_id]["quantity"] <= 0:
        del inventory["items"][item_id]
    
    result_message = f"Equipou {item['name']}."
    
    return inventory, character_stats, result_message

def get_inventory_summary(inventory):
    """
    Get a summary of the inventory contents
    
    Args:
        inventory (dict): The inventory dictionary
        
    Returns:
        str: A formatted summary of the inventory
    """
    try:
        # Verificar se o inventário tem a estrutura correta
        if not isinstance(inventory, dict):
            logger.error(f"Inventário inválido em get_inventory_summary: {inventory}")
            return "Inventário vazio ou com problema."
            
        # Garantir que todas as chaves existam
        if "gold" not in inventory:
            inventory["gold"] = 0
        if "capacity" not in inventory:
            inventory["capacity"] = {"current_weight": 0, "max_weight": 50}
        if "current_weight" not in inventory["capacity"]:
            inventory["capacity"]["current_weight"] = 0
        if "max_weight" not in inventory["capacity"]:
            inventory["capacity"]["max_weight"] = 50
        if "equipped" not in inventory:
            inventory["equipped"] = {"weapon": None, "armor": None, "accessory": None}
        if "items" not in inventory:
            inventory["items"] = {}
        
        gold = inventory["gold"]
        weight = inventory["capacity"]["current_weight"]
        max_weight = inventory["capacity"]["max_weight"]
        
        summary = f"Ouro: {gold}\n"
        summary += f"Peso: {weight}/{max_weight}\n\n"
        
        # Add equipped items
        summary += "Equipado:\n"
        for slot, item_id in inventory["equipped"].items():
            if item_id and item_id in BASE_ITEMS:
                item_name = BASE_ITEMS[item_id]["name"]
                summary += f"  {slot.capitalize()}: {item_name}\n"
            else:
                summary += f"  {slot.capitalize()}: Nada equipado\n"
        
        summary += "\nItens:\n"
        
        # Se não houver itens, indicar isso
        if not inventory["items"]:
            summary += "  Nenhum item na mochila.\n"
            return summary
        
        # Group items by category
        items_by_category = {}
        for item_id, item_data in inventory["items"].items():
            # Skip if item_id not in BASE_ITEMS
            if item_id not in BASE_ITEMS:
                logger.warning(f"Item desconhecido no inventário: {item_id}")
                continue
                
            category = BASE_ITEMS[item_id]["category"]
            if category not in items_by_category:
                items_by_category[category] = []
            
            items_by_category[category].append({
                "id": item_id,
                "name": BASE_ITEMS[item_id]["name"],
                "quantity": item_data.get("quantity", 1)
            })
        
        # Se não houver itens válidos, indicar isso
        if not items_by_category:
            summary += "  Nenhum item válido na mochila.\n"
            return summary
        
        # Add items by category
        for category, items in items_by_category.items():
            category_name = ITEM_CATEGORIES.get(category, category.capitalize())
            summary += f"  {category_name}:\n"
            
            for item in items:
                summary += f"    {item['name']} (x{item['quantity']})\n"
        
        return summary
    except Exception as e:
        logger.error(f"Erro ao gerar resumo do inventário: {e}")
        return "Inventário indisponível no momento. (Erro ao processar)"

def generate_inventory_prompt(character_name, inventory):
    """
    Generate a prompt for the LLM to describe the inventory
    
    Args:
        character_name (str): The character's name
        inventory (dict): The inventory dictionary
        
    Returns:
        str: A prompt for the LLM
    """
    inventory_summary = get_inventory_summary(inventory)
    
    prompt = f"Você é {character_name}, um aventureiro em uma jornada épica. "
    prompt += "Você está olhando para sua mochila e inventário. "
    prompt += f"Aqui está o que você tem:\n\n{inventory_summary}\n\n"
    prompt += "Descreva o conteúdo da sua mochila de forma detalhada."
    
    return prompt

def get_inventory_display(character_name, inventory, include_image=True):
    """
    Get a display of the inventory with AI-generated description
    
    Args:
        character_name (str): The character's name
        inventory (dict): The inventory dictionary
        include_image (bool): Whether to include an AI-generated image
        
    Returns:
        dict: Inventory display data with text and optionally an image
    """
    try:
        # Verificar se o inventário tem a estrutura correta
        if not isinstance(inventory, dict):
            logger.error(f"Inventário inválido: {inventory}")
            return {
                "text": "Seu inventário parece estar vazio ou corrompido. (Erro ao processar inventário)",
                "summary": "Inventário vazio ou com problema."
            }
            
        # Inicializar inventário se estiver faltando dados
        if "items" not in inventory:
            inventory["items"] = {}
        if "equipped" not in inventory:
            inventory["equipped"] = {
                "weapon": None,
                "armor": None,
                "accessory": None
            }
        if "gold" not in inventory:
            inventory["gold"] = 0
        if "capacity" not in inventory:
            inventory["capacity"] = {
                "current_weight": 0,
                "max_weight": 50
            }
        
        # Gerar descrição do inventário
        prompt = generate_inventory_prompt(character_name, inventory)
        inventory_description = generate_text_response(prompt)
        
        result = {
            "text": inventory_description,
            "summary": get_inventory_summary(inventory)
        }
        
        if include_image:
            image_prompt = f"{character_name}, um aventureiro, Uma mochila ou inventário aberto mostrando vários itens de fantasia. Cena de jogo RPG, ambientação de fantasia."
            result["image_url"] = generate_image(image_prompt)
        
        return result
    except Exception as e:
        logger.error(f"Erro ao processar inventário: {e}")
        return {
            "text": "Você verifica sua mochila, mas está muito escuro para ver os itens claramente. (Erro ao processar comando)",
            "summary": "Erro ao processar inventário"
        }

def save_inventory_to_file(inventory, character_id):
    """
    Save the inventory to a JSON file
    
    Args:
        inventory (dict): The inventory dictionary
        character_id (int): The character's ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        filename = f"inventory_{character_id}.json"
        with open(filename, "w") as f:
            json.dump(inventory, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving inventory: {e}")
        return False

def load_inventory_from_file(character_id):
    """
    Load the inventory from a JSON file
    
    Args:
        character_id (int): The character's ID
        
    Returns:
        dict: The loaded inventory, or a new one if the file doesn't exist
    """
    try:
        filename = f"inventory_{character_id}.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                inventory = json.load(f)
            return inventory
        else:
            return initialize_inventory(character_id)
    except Exception as e:
        logger.error(f"Error loading inventory: {e}")
        return initialize_inventory(character_id)