import json
import random

class GameEngine:
    def __init__(self):
        self.world_data = {}
        self.npcs = {}
        self.quests = {}
        
    def initialize_game_world(self):
        """Initialize the game world with locations, NPCs, and quests."""
        # Define game world locations
        self.world_data = {
            "starting_village": {
                "name": "Meadowbrook",
                "description": "A peaceful village with thatched-roof cottages and friendly villagers.",
                "connections": ["forest_path", "village_tavern", "marketplace"],
                "npcs": ["village_elder", "blacksmith", "innkeeper"]
            },
            "forest_path": {
                "name": "Whisperwind Forest",
                "description": "A dense forest with tall trees and mysterious sounds.",
                "connections": ["starting_village", "ancient_ruins", "river_crossing"],
                "npcs": ["wandering_merchant", "forest_witch"]
            },
            "ancient_ruins": {
                "name": "Ruins of Eldrath",
                "description": "Crumbling stone structures from a forgotten civilization.",
                "connections": ["forest_path", "underground_chamber"],
                "npcs": ["ghostly_figure", "treasure_hunter"]
            },
            "village_tavern": {
                "name": "The Prancing Pony",
                "description": "A warm, lively tavern with good food and interesting patrons.",
                "connections": ["starting_village"],
                "npcs": ["bard", "mysterious_stranger", "drunk_adventurer"]
            },
            "marketplace": {
                "name": "Meadowbrook Market",
                "description": "A bustling market with various vendors selling goods.",
                "connections": ["starting_village"],
                "npcs": ["potion_vendor", "weapon_merchant", "jewelry_crafter"]
            },
            "river_crossing": {
                "name": "Silvermist River",
                "description": "A wide river with a stone bridge crossing it.",
                "connections": ["forest_path", "mountain_path"],
                "npcs": ["fisherman", "bridge_troll"]
            },
            "mountain_path": {
                "name": "Frostpeak Trail",
                "description": "A rocky path winding up the mountainside.",
                "connections": ["river_crossing", "mountain_cave"],
                "npcs": ["mountain_guide", "injured_climber"]
            },
            "mountain_cave": {
                "name": "Dragon's Lair",
                "description": "A massive cave with evidence of a large creature living inside.",
                "connections": ["mountain_path"],
                "npcs": ["ancient_dragon"]
            },
            "underground_chamber": {
                "name": "Crystal Caverns",
                "description": "A beautiful underground chamber filled with glowing crystals.",
                "connections": ["ancient_ruins"],
                "npcs": ["cave_dweller", "crystal_guardian"]
            }
        }
        
        # Define NPCs
        self.npcs = {
            "village_elder": {
                "name": "Elder Thorne",
                "description": "A wise old man with a long white beard and kind eyes.",
                "dialog": "Welcome to Meadowbrook, traveler. Our village could use someone with your skills."
            },
            "blacksmith": {
                "name": "Gorin Ironhammer",
                "description": "A muscular dwarf with a soot-covered apron and a hearty laugh.",
                "dialog": "Need a new blade? I forge the finest weapons in the region!"
            },
            "innkeeper": {
                "name": "Mabel Sweetwater",
                "description": "A plump, cheerful woman who runs the village inn.",
                "dialog": "Welcome to the Golden Goose Inn! We have warm beds and hot meals."
            },
            "wandering_merchant": {
                "name": "Silvan",
                "description": "A lanky man with a heavily-laden pack and a shrewd smile.",
                "dialog": "Rare goods from distant lands! Take a look at my wares, friend."
            },
            "forest_witch": {
                "name": "Willow",
                "description": "An ageless woman with green eyes and clothes made of leaves and vines.",
                "dialog": "The forest speaks of your arrival. Perhaps you are the one foretold in my visions."
            },
            "ghostly_figure": {
                "name": "The Archivist",
                "description": "A translucent figure in ancient scholarly robes.",
                "dialog": "Seeker of knowledge... these ruins hold dangerous secrets. Proceed with caution."
            },
            "treasure_hunter": {
                "name": "Caleb Drake",
                "description": "A rugged man with a scar across his face and well-worn expedition gear.",
                "dialog": "This place is filled with traps and puzzles. I've been trying to reach the central chamber for weeks."
            },
            "bard": {
                "name": "Melody Silverharp",
                "description": "A charismatic elf with a beautiful voice and an ornate lute.",
                "dialog": "Care to hear a tale of ancient heroes? Or perhaps you'll create a legend of your own!"
            },
            "mysterious_stranger": {
                "name": "The Hooded One",
                "description": "A cloaked figure sitting alone in the corner, face obscured.",
                "dialog": "You have the look of someone searching for something. Perhaps we can help each other..."
            }
        }
        
        # Define quests
        self.quests = {
            "village_troubles": {
                "name": "Village Troubles",
                "giver": "village_elder",
                "description": "The village has been experiencing strange occurrences lately. Investigate the cause.",
                "objectives": ["speak_to_witnesses", "check_forest_edge", "confront_culprit"],
                "rewards": {"exp": 100, "gold": 50}
            },
            "missing_shipment": {
                "name": "The Missing Shipment",
                "giver": "blacksmith",
                "description": "A shipment of rare metals hasn't arrived. Find out what happened to it.",
                "objectives": ["check_road", "find_cart", "deal_with_bandits"],
                "rewards": {"exp": 150, "gold": 75, "item": "quality_hammer"}
            },
            "forest_spirits": {
                "name": "Appeasing the Forest Spirits",
                "giver": "forest_witch",
                "description": "The forest spirits are restless. Gather ingredients for a calming ritual.",
                "objectives": ["gather_moonflowers", "collect_clear_water", "find_ancient_stone", "return_to_witch"],
                "rewards": {"exp": 200, "gold": 50, "item": "nature_amulet"}
            }
        }
    
    def process_command(self, command, character, game_state):
        """Process a player command and update game state accordingly."""
        command = command.lower().strip()
        result = {
            "context": "",
            "new_location": None,
            "image_prompt": ""
        }
        
        # Get current location data
        current_location = game_state.current_location
        location_data = self.world_data.get(current_location, {})
        
        # Process movement commands
        if command.startswith("go to ") or command.startswith("travel to ") or command.startswith("visit "):
            destination = command.split(" to " if " to " in command else " ")[-1].strip()
            
            # Check if destination is a valid connection
            for connection in location_data.get("connections", []):
                conn_name = self.world_data[connection]["name"].lower()
                if destination in conn_name.lower() or destination in connection.lower():
                    # Valid movement
                    result["new_location"] = connection
                    new_location_data = self.world_data[connection]
                    result["context"] = f"You have arrived at {new_location_data['name']}. {new_location_data['description']}"
                    result["image_prompt"] = f"A view of {new_location_data['name']}, {new_location_data['description']}"
                    return result
            
            # Invalid movement
            result["context"] = f"You cannot go to {destination} from here. Available locations: " + ", ".join([self.world_data[conn]["name"] for conn in location_data.get("connections", [])])
            result["image_prompt"] = f"A confused adventurer in {location_data.get('name', 'the current location')}, looking at a map"
            return result
            
        # Process talk/speak commands
        elif command.startswith("talk to ") or command.startswith("speak to ") or command.startswith("talk with "):
            npc_name = command.split(" to " if " to " in command else " with ")[-1].strip()
            
            # Check if NPC is in current location
            for npc_id in location_data.get("npcs", []):
                npc_data = self.npcs.get(npc_id, {})
                if npc_name in npc_data.get("name", "").lower() or npc_name in npc_id.lower():
                    # Valid NPC interaction
                    result["context"] = f"You approach {npc_data['name']}. {npc_data['description']} The NPC says: '{npc_data['dialog']}'"
                    result["image_prompt"] = f"A character talking to {npc_data['name']}, {npc_data['description']}, in {location_data.get('name', 'the current location')}"
                    return result
            
            # Invalid NPC
            result["context"] = f"There is no one called {npc_name} here. Available NPCs: " + ", ".join([self.npcs[npc]["name"] for npc in location_data.get("npcs", [])])
            result["image_prompt"] = f"A character looking around for someone in {location_data.get('name', 'the current location')}"
            return result
            
        # Process look/examine commands
        elif command.startswith("look") or command.startswith("examine") or command == "look around":
            result["context"] = f"You are in {location_data.get('name', 'an unknown location')}. {location_data.get('description', '')} You can see: " + ", ".join([self.npcs[npc]["name"] for npc in location_data.get("npcs", [])])
            result["image_prompt"] = f"A detailed view of {location_data.get('name', 'the current location')}, {location_data.get('description', '')}"
            return result
            
        # Process help command
        elif command == "help":
            result["context"] = """Available commands:
            - go to [location]: Travel to a connected location
            - talk to [npc]: Speak with an NPC
            - look/examine: Examine your surroundings
            - help: Show this help message
            - inventory: Check your inventory
            - status: Check your character status"""
            result["image_prompt"] = f"A scroll or book showing a list of commands, in a fantasy setting"
            return result
            
        # Process inventory command
        elif command == "inventory":
            inventory = json.loads(game_state.inventory)
            if inventory:
                items_list = ", ".join([f"{count}x {item}" for item, count in inventory.items()])
                result["context"] = f"Your inventory contains: {items_list}"
            else:
                result["context"] = "Your inventory is empty."
            result["image_prompt"] = f"An open backpack or inventory of {character.name} showing various fantasy items"
            return result
            
        # Process status command
        elif command == "status" or command == "character" or command == "stats":
            result["context"] = f"""
            Name: {character.name}
            Class: {character.character_class}
            Level: {character.level}
            Experience: {character.experience}
            Health: {character.health}/100
            Mana: {character.mana}/100
            Strength: {character.strength}
            Intelligence: {character.intelligence}
            Dexterity: {character.dexterity}
            """
            result["image_prompt"] = f"A character sheet or status screen showing {character.name}, a {character.character_class}"
            return result
            
        # Generic response for unrecognized commands
        else:
            # Send the command to AI service for interpretation
            result["context"] = f"You attempt to {command} in {location_data.get('name', 'the current location')}."
            result["image_prompt"] = f"Character attempting to {command} in {location_data.get('name', 'the current location')}"
            return result
