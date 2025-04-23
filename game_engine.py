import json
import random
import logging
import datetime

# Import our custom modules
import game_world
import game_objectives
import inventory_system
import filtering_toxicity
from ai_service import generate_text_response, generate_image

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GameEngine:
    def __init__(self):
        self.world_data = {}
        self.npcs = {}
        self.quests = {}
        self.time_of_day = "morning"
        self.game_day = 1
        self.game_hour = 8  # Start at 8 AM
        
    def initialize_game_world(self):
        """Initialize the game world with locations, NPCs, and quests."""
        # Use our game_world module to get the game world data
        self.world_data = game_world.LOCATIONS
        self.npcs = game_world.NPCS
        
        # Get quest data from game_objectives module
        self.main_quests = game_objectives.MAIN_QUESTS
        self.side_quests = game_objectives.SIDE_QUESTS
        
        # Combine all quests into a single dictionary for easier access
        self.quests = {}
        for quest in self.main_quests:
            self.quests[quest["id"]] = quest
        for quest in self.side_quests:
            self.quests[quest["id"]] = quest
            
        # Initialize game time
        self.game_hour = game_world.GAME_RULES["time"]["starting_hour"]
        self.game_day = 1
        self.update_time_of_day()
        
    def update_time_of_day(self):
        """Update the time of day based on the current game hour."""
        if 5 <= self.game_hour < 12:
            self.time_of_day = "morning"
        elif 12 <= self.game_hour < 17:
            self.time_of_day = "afternoon"
        elif 17 <= self.game_hour < 21:
            self.time_of_day = "evening"
        else:
            self.time_of_day = "night"
    
    def advance_game_time(self, hours):
        """Advance the game time by a number of hours."""
        self.game_hour += hours
        
        # Handle day change
        while self.game_hour >= 24:
            self.game_hour -= 24
            self.game_day += 1
            
        # Update time of day
        self.update_time_of_day()

    def process_command(self, command, character, game_state): #TODO: make an LLM Agent to handle the commands. Be sure the commands provided by the LLM fall in the options defined here
        """Process a player command and update game state accordingly."""
        # First, check if the command contains any content that should be filtered
        is_appropriate, rejection_message = filtering_toxicity.check_player_input(command)
        if not is_appropriate:
            return {
                "context": rejection_message,
                "new_location": None,
                "image_prompt": "Um aventureiro em uma floresta pacífica"  # Safe default image
            }
            
        command = command.lower().strip()
        result = {
            "context": "",
            "new_location": None,
            "image_prompt": ""
        }
        
        # Get current location data
        current_location = game_state.current_location
        if current_location in self.world_data:
            location_data = self.world_data[current_location]
            location_description = game_world.get_location_description(current_location, self.time_of_day)
        else:
            # Fallback to Meadowbrook if location not found
            current_location = game_world.WORLD_CONFIG["starting_location"]
            location_data = self.world_data[current_location]
            location_description = game_world.get_location_description(current_location, self.time_of_day)
            game_state.current_location = current_location
        
        # Check for quests available in this location
        available_quests = []
        if "quests" in location_data:
            for quest_id in location_data["quests"]:
                quest = game_objectives.get_quest_by_id(quest_id)
                if quest:
                    available_quests.append(quest)
        
        # Process movement commands (in Portuguese)
        if (command.startswith("ir para ") or command.startswith("viajar para ") or 
            command.startswith("visitar ") or command.startswith("ir a ")):
            destination = command.split(" para " if " para " in command else " a " if " a " in command else " ")[-1].strip()
            
            # Check if destination is a valid connection
            for connection in location_data.get("connections", []):
                conn_name = self.world_data[connection]["name"].lower()
                if destination in conn_name.lower() or destination in connection.lower():
                    # Valid movement - advance game time
                    self.advance_game_time(1)  # 1 hour to travel
                    
                    # Valid movement
                    result["new_location"] = connection
                    new_location_data = self.world_data[connection]
                    new_location_description = game_world.get_location_description(connection, self.time_of_day)
                    
                    result["context"] = f"Você chegou a {new_location_data['name']}. {new_location_description}"
                    result["image_prompt"] = game_world.get_location_image_prompt(connection, self.time_of_day, character)
                    return result
            
            # Invalid movement
            result["context"] = f"Você não pode ir para {destination} daqui. Locais disponíveis: " + ", ".join([self.world_data[conn]["name"] for conn in location_data.get("connections", [])])
            result["image_prompt"] = f"Um aventureiro confuso em {location_data.get('name', 'o local atual')}, olhando para um mapa" #TODO: adjust the image to a default one without generating           
            return result
            
        # Process talk/speak commands
        elif (command.startswith("falar com ") or command.startswith("conversar com ") or 
              command.startswith("perguntar a ")):
            npc_name = command.split(" com " if " com " in command else " a ")[-1].strip()
            
            # Check if NPC is in current location
            for npc_id in location_data.get("npcs", []):
                npc_data = self.npcs.get(npc_id, {})
                if npc_name in npc_data.get("name", "").lower() or npc_name in npc_id.lower():
                    # Valid NPC interaction
                    # Get the appropriate dialogue type
                    dialogue_type = "greeting"
                    
                    # Check if NPC offers quests
                    if "quests" in npc_data:
                        for quest_id in npc_data["quests"]:
                            quest = game_objectives.get_quest_by_id(quest_id)
                            if quest:
                                # If player doesn't have this quest yet, offer it
                                quest_progress = json.loads(game_state.quest_progress)
                                if "completed_quests" in quest_progress and quest_id not in quest_progress["completed_quests"]:
                                    dialogue_type = "quest_offer"
                    
                    dialogue = game_world.generate_npc_dialogue(npc_id, dialogue_type, character.__dict__)
                    
                    result["context"] = f"Você se aproxima de {npc_data['name']}. {npc_data['description']} O NPC diz: '{dialogue}'"
                    result["image_prompt"] = f"{character.name}, um aventureiro, conversando com {npc_data['name']}, {npc_data['description']}, em {location_data.get('name', 'o local atual')}"
                    return result
            
            # Invalid NPC #TODO: Let the LLM handle the command to get NPC name
            result["context"] = f"Não há ninguém chamado {npc_name} aqui. NPCs disponíveis: " + ", ".join([self.npcs[npc]["name"] for npc in location_data.get("npcs", [])])
            result["image_prompt"] = f"Um aventureiro procurando por alguém em {location_data.get('name', 'o local atual')}"
            return result
            
        # Process look/examine commands
        elif (command.startswith("olhar") or command.startswith("examinar") or command == "olhar ao redor" or
             command == "observar" or command == "ver"):
            npcs_here = []
            if "npcs" in location_data:
                npcs_here = [self.npcs[npc]["name"] for npc in location_data.get("npcs", []) if npc in self.npcs]
            
            if npcs_here:
                result["context"] = f"Você está em {location_data.get('name', 'um lugar desconhecido')}. {location_description} Você pode ver: {', '.join(npcs_here)}."
            else:
                result["context"] = f"Você está em {location_data.get('name', 'um lugar desconhecido')}. {location_description} Não há ninguém por perto."
                
            result["image_prompt"] = game_world.get_location_image_prompt(current_location, self.time_of_day, character.__dict__)
            return result
            
        # Process help command 
        elif command == "ajuda" or command == "help":
            result["context"] = """Comandos disponíveis:
            - ir para [local]: Viajar para um local conectado
            - falar com [npc]: Conversar com um NPC
            - olhar/examinar: Examinar seus arredores
            - ajuda: Mostrar esta mensagem de ajuda
            - inventário: Verificar seu inventário
            - status: Verificar o status do seu personagem
            - missões: Ver suas missões atuais
            - descansar: Descansar para recuperar saúde e mana
            - equipar [item]: Equipar um item do seu inventário
            - usar [item]: Usar um item do seu inventário"""
            result["image_prompt"] = f"Um pergaminho ou livro mostrando uma lista de comandos, em um cenário de fantasia"
            return result
            
        # Process inventory command
        elif command == "inventário" or command == "inventory" or command == "itens" or command == "mochila":
            # Use our inventory system to get a nice display
            try:
                # Verificar se o inventário existe e é válido
                inventory_data = {}
                if not game_state.inventory:
                    logging.warning(f"Inventário vazio para personagem {character.id} ao processar comando")
                    inventory_data = inventory_system.initialize_inventory(character.id)
                    game_state.inventory = json.dumps(inventory_data)
                else:
                    try:
                        inventory_data = json.loads(game_state.inventory)
                        if not isinstance(inventory_data, dict):
                            raise ValueError("Formato de inventário inválido")
                    except (json.JSONDecodeError, ValueError) as e:
                        logging.error(f"Erro ao carregar inventário: {e}")
                        inventory_data = inventory_system.initialize_inventory(character.id)
                        game_state.inventory = json.dumps(inventory_data)
                
                # Obter a exibição do inventário com tratamento de exceções
                inventory_display = inventory_system.get_inventory_display(character.name, inventory_data)
                
                result["context"] = inventory_display["text"]
                result["image_prompt"] = inventory_display.get("image_url", f"{character.name}, um aventureiro, Uma mochila ou inventário aberto mostrando vários itens de fantasia")
                return result
            except Exception as e:
                logging.error(f"Erro ao processar comando de inventário: {e}")
                result["context"] = "Você tenta verificar seu inventário, mas sua mochila parece estar presa. (Erro ao processar comando de inventário)"
                result["image_prompt"] = f"{character.name} tentando abrir uma mochila presa"
                return result
            
        # Process status command
        elif command == "status" or command == "personagem" or command == "atributos" or command == "stats":
            class_name = game_world.CHARACTER_CLASSES[character.character_class]["name"]
            
            result["context"] = f"""
            Nome: {character.name}
            Classe: {class_name}
            Nível: {character.level}
            Experiência: {character.experience}
            Saúde: {character.health}/100
            Mana: {character.mana}/100
            Força: {character.strength}
            Inteligência: {character.intelligence}
            Destreza: {character.dexterity}
            """
            result["image_prompt"] = f"{character.name}, um {class_name}, posando heroicamente, mostrando seus atributos e equipamentos"
            return result
            
        # Process quests command
        elif command == "missões" or command == "quests" or command == "objetivos":
            # Parse quest progress from game state
            quest_progress = json.loads(game_state.quest_progress)
            completed_quests = quest_progress.get("completed_quests", [])
            
            # Get available quests for this character
            available_quests = game_objectives.get_available_quests(
                character.level, 
                completed_quests, 
                current_location
            )
            
            if not available_quests:
                result["context"] = "Você não tem missões ativas no momento."
            else:
                quest_text = "Suas missões atuais:\n\n"
                for quest in available_quests:
                    quest_text += f"- {quest['title']}: {quest['description']}\n  Objetivo: {quest['objective']}\n\n"
                result["context"] = quest_text
                
            result["image_prompt"] = f"{character.name}, um aventureiro, olhando para um pergaminho de missões em {location_data.get('name', 'o local atual')}"
            return result
            
        # Process rest command
        elif command == "descansar" or command == "dormir" or command == "acampar" or command == "rest":
            # Check if location is safe for resting
            danger_level = location_data.get("danger_level", 0)
            
            if danger_level >= 4:
                result["context"] = "Este local é muito perigoso para descansar. Encontre um lugar mais seguro."
                result["image_prompt"] = f"{character.name} incapaz de descansar em um lugar perigoso"
                return result
                
            # Advance game time
            self.advance_game_time(8)  # 8 hours of rest
            
            # Calculate recovery based on game rules
            health_recovery = int(100 * game_world.GAME_RULES["rest"]["health_recovery"])
            mana_recovery = int(100 * game_world.GAME_RULES["rest"]["mana_recovery"])
            
            character.health = min(100, character.health + health_recovery)
            character.mana = min(100, character.mana + mana_recovery)
            
            result["context"] = f"Você descansou por algumas horas. Recuperou {health_recovery} de saúde e {mana_recovery} de mana. Agora é {self.time_of_day}."
            result["image_prompt"] = f"{character.name} descansando em um acampamento durante o {self.time_of_day} em {location_data.get('name', 'um local')}"
            return result
        
        # Process equip command
        elif command.startswith("equipar ") or command.startswith("equip "):
            try:
                item_name = command.split(" ", 1)[1].strip()
                
                # Verificar se o inventário existe e é válido
                inventory_data = {}
                try:
                    if not game_state.inventory:
                        logging.warning(f"Inventário vazio para personagem {character.id} ao equipar item")
                        inventory_data = inventory_system.initialize_inventory(character.id)
                        game_state.inventory = json.dumps(inventory_data)
                    else:
                        inventory_data = json.loads(game_state.inventory)
                        if not isinstance(inventory_data, dict):
                            raise ValueError("Formato de inventário inválido")
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"Erro ao carregar inventário para equipar item: {e}")
                    inventory_data = inventory_system.initialize_inventory(character.id)
                    game_state.inventory = json.dumps(inventory_data)
                
                # Find the item_id from the name
                item_id = None
                for id, item in inventory_system.BASE_ITEMS.items():
                    if item["name"].lower() == item_name.lower():
                        item_id = id
                        break
                
                if not item_id or item_id not in inventory_data.get("items", {}):
                    result["context"] = f"Você não tem {item_name} no seu inventário."
                    result["image_prompt"] = f"{character.name} procurando por {item_name} na mochila sem sucesso"
                    return result
                    
                # Equip the item
                inventory_data, character_stats, message = inventory_system.equip_item(
                    inventory_data, 
                    item_id, 
                    character.__dict__
                )
                
                # Update game state with new inventory
                game_state.inventory = json.dumps(inventory_data)
                
                result["context"] = message
                result["image_prompt"] = f"{character.name} equipando {item_name} em {location_data.get('name', 'o local atual')}"
                return result
            except Exception as e:
                logging.error(f"Erro ao processar comando de equipar: {e}")
                result["context"] = f"Você tenta equipar algo, mas encontra dificuldade. (Erro ao processar comando)"
                result["image_prompt"] = f"{character.name} com dificuldade para manusear equipamentos"
                return result
            
        # Process use item command
        elif command.startswith("usar ") or command.startswith("use ") or command.startswith("beber ") or command.startswith("comer "):
            try:
                item_name = command.split(" ", 1)[1].strip()
                
                # Verificar se o inventário existe e é válido
                inventory_data = {}
                try:
                    if not game_state.inventory:
                        logging.warning(f"Inventário vazio para personagem {character.id} ao usar item")
                        inventory_data = inventory_system.initialize_inventory(character.id)
                        game_state.inventory = json.dumps(inventory_data)
                    else:
                        inventory_data = json.loads(game_state.inventory)
                        if not isinstance(inventory_data, dict):
                            raise ValueError("Formato de inventário inválido")
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"Erro ao carregar inventário para usar item: {e}")
                    inventory_data = inventory_system.initialize_inventory(character.id)
                    game_state.inventory = json.dumps(inventory_data)
                
                # Find the item_id from the name
                item_id = None
                for id, item in inventory_system.BASE_ITEMS.items():
                    if item["name"].lower() == item_name.lower():
                        item_id = id
                        break
                
                if not item_id or item_id not in inventory_data.get("items", {}):
                    result["context"] = f"Você não tem {item_name} no seu inventário."
                    result["image_prompt"] = f"{character.name} procurando por {item_name} na mochila sem sucesso"
                    return result
                    
                # Use the item
                inventory_data, character_stats, message = inventory_system.use_item(
                    inventory_data, 
                    item_id, 
                    character.__dict__
                )
                
                # Update character stats
                if character_stats:
                    if "health" in character_stats:
                        character.health = character_stats["health"]
                    if "mana" in character_stats:
                        character.mana = character_stats["mana"]
                
                # Update game state with new inventory
                game_state.inventory = json.dumps(inventory_data)
                
                result["context"] = message
                result["image_prompt"] = f"{character.name} usando {item_name} em {location_data.get('name', 'o local atual')}"
                return result
            except Exception as e:
                logging.error(f"Erro ao processar comando de usar item: {e}")
                result["context"] = f"Você tenta usar um item, mas algo dá errado. (Erro ao processar comando)"
                result["image_prompt"] = f"{character.name} com dificuldade para usar um item em sua mochila"
                return result
            
        # Generic response for unrecognized commands
        else:
            # First check if the command should be filtered
            safe_command = filtering_toxicity.safe_ai_request(
                f"O jogador diz: '{command}' no RPG",
                lambda x: x  # Identity function since we're just filtering
            )
            
            # Send the command to AI service for interpretation (with safety)
            prompt = f"Você é {character.name}, um aventureiro em {location_data.get('name', 'um local desconhecido')}. Você tenta: {safe_command}. Descreva o resultado dessa ação no contexto do mundo de fantasia e do local atual."
            
            ai_response = filtering_toxicity.safe_ai_request(
                prompt,
                generate_text_response
            )
            
            result["context"] = ai_response
            result["image_prompt"] = f"{character.name} tentando {safe_command} em {location_data.get('name', 'o local atual')}"
            return result
            
